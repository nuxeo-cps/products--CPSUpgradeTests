import os
import unittest
import datetime
import transaction

import Globals
from Testing.ZopeTestCase import ZopeTestCase, installProduct

from Products.GenericSetup.interfaces import EXTENSION
from Products.CPSCore.setuptool import CPSSetupTool

# Install all CPS products that have GenericSetup support:
installProduct('CPSBlog')
installProduct('CPSBoxes')
installProduct('CPSChat')
installProduct('CPSCollector')
installProduct('CPSCore')
installProduct('CPSDefault')
installProduct('CPSDocument')
installProduct('CPSForum')
installProduct('CPSMailAccess')
installProduct('CPSNewsLetters')
installProduct('CPSOoo')
installProduct('CPSPortlets')
installProduct('CPSRelation')
installProduct('CPSRemoteController')
installProduct('CPSRSS')
installProduct('CPSSchemas')
installProduct('CPSSharedCalendar')
installProduct('CPSSkins')
installProduct('CPSSubscriptions')
installProduct('CPSTypeMaker')
installProduct('CPSWiki')
installProduct('CPSWorkflow')

# Some non CPS Products have to be installed for installs/upgrades to work, 
# although they do not have any profiles or upgrades by themselves.
# For CPSDefault install:
installProduct('ZCTextIndex')
installProduct('CMFCore')
# For CPSSharedCalendar install
installProduct('CalZope') 
installProduct('CPSonFive')

# Finally, we install Five, which will load all the insalled products ZCML.
installProduct('Five') 


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

    def _createSetupTool(self):
        self.app.cps.manage_addProduct['CPSCore'].manage_addTool(
            CPSSetupTool.meta_type)
        
    def _doAllUpgrades(self):
        setuptool = self.app.cps.portal_setup
        upgrades = [u['id'] for u in setuptool.listUpgrades() if u['proposed']]
        if upgrades:
            setuptool.doUpgrades(upgrades)        

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
        
    def _verifyPublishing(self):
        doc = self.app.cps.workspaces.test_workspace.test_document
        content = doc.getContent().aq_base
        
        root_section = self.app.cps.sections
        test_section = root_section.test_section
        self.failUnless(root_section.test_document.getContent().aq_base
                        is content)
        self.failUnless(test_section.test_document.getContent().aq_base
                        is content)
        


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
    # XXX This is not actually used yet
    def _upgrade(self):
        # 1. Create a before upgrade snapshot.
        self._createSnapshot('before-upgrade')
        
        # 2. Go to the portal_setup and run all proposed upgrades.
        self._doAllUpgrades()
            
        # 3. Finally, we make a snapshot
        self._createSnapshot('before-upgrade')
                