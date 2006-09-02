import os
import unittest
import datetime
import transaction

import Globals

from Testing.ZopeTestCase import ZopeTestCase, installProduct

from Products.GenericSetup.interfaces import EXTENSION
from Products.CPSCore.setuptool import CPSSetupTool

# Install all Products:
import OFS.Application
products = OFS.Application.get_products()
for product in products:
    installProduct(product[1], 1)

class UpgradeTestCase(ZopeTestCase):

    # We need to have thee name of the directory that keeps the Data.fs,
    # so we can check that the test is run with the right Data.fs. Since
    # each test test a specific CPS version, you would get false errors
    # if run with the wrong Data.fs.
    db_dir = None

    def beforeSetUp(self):
        self._checkDB()
        transaction.begin()

    def afterSetUp(self):
        # Set the folder to be the portal, so we can log in.
        self.folder = self.app.cps
        self.login('manager')

        # Enable the local site:
        from Products.Five.site.localsite import enableLocalSiteHook
        from zope.app.component.hooks import setHooks, setSite
        setHooks()
        enableLocalSiteHook(self.folder)
        setSite(self.folder)

    def _createSetupTool(self):
        self.app.cps.manage_addProduct['CPSCore'].manage_addTool(
            CPSSetupTool.meta_type)

    def _doAllUpgrades(self):
        from Products.CPSCore.upgrade import _categories_registry
        categories = _categories_registry.keys()
        setuptool = self.app.cps.portal_setup
        for cat in categories:
            upgrades = [u['id'] for u in setuptool.listUpgrades(category=cat)
                        if u['proposed']]
            if upgrades:
                setuptool.doUpgrades(upgrades, cat)

    def _installDefaultProfile(self):
        setuptool = self.app.cps.portal_setup
        setuptool.importProfile('profile-CPSDefault:default')

    def _installAllProfilesAndUpgrade(self):
        setuptool = self.app.cps.portal_setup
        all_profiles = [p['id'] for p in setuptool.listProfileInfo()
                        if p['type'] == EXTENSION]
        # There are some profiles that should to be done before others, such
        # as CPSSubscriptions and CPSRelation. Hopefully this will be automatic
        # in the future
        first_profiles = ['CPSSubscriptions:default', 'CPSRelation:default']
        profiles = []
        for profile in first_profiles:
            if profile in all_profiles:
                profiles.append(profile)
                all_profiles.remove(profile)

        # The rest can be added to the end.
        profiles.extend(all_profiles)

        for profile in profiles:
            # Install profiles
            setuptool.importProfile('profile-'+profile)
            # Do upgrades, if any
            self._doAllUpgrades()

    def _createSnapshot(self, id='snappy'):
        setuptool = self.app.cps.portal_setup
        setuptool.createSnapshot(id)

    def _checkDB(self):
        if self.db_dir is None:
            raise "You have not set the db_dir attribute on your test case"
        db_file = Globals.DB._storage._base._file_name
        dir, name = os.path.split(db_file)
        dir, name = os.path.split(dir)
        if name == self.db_dir:
            return True
        raise "This test was run with the wrong database! Please make sure "\
              "that you run the tests with the test_all_upgrades.sh script."

    def _verifyCalendaring(self):
        """Makes sure the calendar now is correctly installed"""

        # Check that the manager really has a personal calendar.
        manager_cal = self.app.cps.portal_cpscalendar.getHomeCalendarObject()
        # It should have two events
        manager_attendee = manager_cal.getMainAttendee()
        events = manager_attendee.getEvents((None,None))
        self.failUnlessEqual(len(events), 2)

        for event in events:
            if event.title == 'Private Event':
                # Make sure the private event is private
                self.failUnlessEqual(event.access, u'PRIVATE')
                self.failUnlessEqual(event.document,
                                     '/cps/workspaces/calendar_document')
            elif event.title == 'Meeting':
                # The meeting should have three attendees
                attendees = event.getAttendeeIds()
                self.failUnlessEqual(len(attendees), 3)
                # Both the resource and the workspace calendar should be
                # attendees to this event
                self.failUnless(
                    'CALENDAR!/cps/workspaces/workspace_calendar' in attendees)
                self.failUnless(
                    'CALENDAR!/cps/workspaces/resource_calendar' in attendees)

        # There should be both workspace and resource calendars as well.
        rescalendar = self.app.cps.workspaces.resource_calendar
        self.failUnlessEqual(rescalendar._attendee_type, 'RESOURCE')

        wscalendar = self.app.cps.workspaces.workspace_calendar
        self.failUnlessEqual(wscalendar._attendee_type, 'WORKSPACE')
        wsattendee = wscalendar.getMainAttendee()
        events = wsattendee.getEvents((None,None))
        self.failUnlessEqual(len(events), 2)

        occurrences = ()
        for event in events:
            if event.title == 'Recurring Event':
                occurrences = event.expand((None, datetime.datetime.max))
        self.failUnlessEqual(len(occurrences), 5)


    def _verifyDocument(self):
        doc = self.app.cps.workspaces.test_workspace.test_document
        content = doc.getContent()
        if getattr(content, 'content', None) is not None:
            # CPS 3.2.4
            main = content.content
            right = content.content_right
            photo = content.photo
        else:
            # CPS 3.3.8
            main = content.content_f0
            right = content.content_right_f0
            photo = content.photo_f0
        self.failUnlessEqual(main, 'Main text')
        self.failUnlessEqual(right, 'Right text')
        self.failIf(photo is None)

    def _verifyNewsItem(self):
        # Make sure News Items are now flexible, and that the file
        # attachement was included.
        # This change happened in version 3.3.1, and
        # the test is not necessary for later versions.
        doc = self.app.cps.workspaces.news_with_file
        content = doc.getContent()
        self.failUnless(content.attachedFile_f0 is not None)
        self.failUnless(content.photo is not None)

    def _checkSubGroupSupport(self):
        groupdir = self.app.cps.portal_directories.groups
        self.failUnless(hasattr(groupdir, 'hasSubGroupsSupport'))

    def _verifyPublishing(self):
        doc = self.app.cps.workspaces.test_workspace.test_document
        content = doc.getContent().aq_base

        root_section = self.app.cps.sections
        test_section = root_section.test_section
        self.failUnless(root_section.test_document.getContent().aq_base
                        is content)
        self.failUnless(test_section.test_document.getContent().aq_base
                        is content)

    def _verifyImageBoxTemplet(self):
        # Take a templet that isn't set by any profile, hence comes straight
        # from the upgrade procedure
        templet = self.app.unrestrictedTraverse(
            'cps/portal_themes/lightskins/1512532755/1060267354/1060893038')

        self.assertEquals(templet.objectIds(), ['image'])
        self.assertEquals(templet.image.size, 16594)

    def _verifyFolderDestruction(self):
        sections = self.app.cps.sections
        sections.folder_delete(['test_section'])
        import transaction
        transaction.commit() # error would be here


class PreGenericSetupTestCase(UpgradeTestCase):
    """Tests upgrades from versions of CPS before Genericsetup support
    """

    def _upgrade(self):
        # 1. Create the portal_setup tool
        self._createSetupTool()

        # 2. Go to the portal_setup and run all proposed upgrades.
        self._doAllUpgrades()
        # The user folder has now been replaced, so we need to login again.
        self.login('manager')

        # 3. Install the default profile.
        self._installDefaultProfile()

        # 4. Set the membersfolder to it's old location:
        self.app.cps.portal_membership.setMembersFolderById(
            'workspaces/members')

        # 5 Check for new proposed upgrades
        self._doAllUpgrades()

        # 6. Install all available extension profiles, and see if there
        #    are new upgrades to do after each profile install.
        self._installAllProfilesAndUpgrade()

        # 7. Finally, we make a snapshot
        self._createSnapshot()


class PostGenericSetupTestCase(UpgradeTestCase):
    """Tests upgrades from versions of CPS with Genericsetup support
    """
    def _upgrade(self):
        # 1. Create a before upgrade snapshot.
        self._createSnapshot('before-upgrade')

        # 2. Go to the portal_setup and run all proposed upgrades.
        self._doAllUpgrades()

        # 3. Finally, we make a snapshot
        self._createSnapshot('after-upgrade')

