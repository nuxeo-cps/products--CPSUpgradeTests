import os
import unittest

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

    def afterSetUp(self):
        # Set the folder to be the portal, so we can log in.
        self.folder = self.app.cps
        self.login('root')

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


class PreGenericSetupTestCase(UpgradeTestCase):
    """Tests upgrades from versions of CPS before Genericsetup support
    """
                
    def _upgrade(self):
        # 1. Create the portal_setup tool
        self._createSetupTool()
        
        # 2. Go to the portal_setup and run all proposed upgrades.
        self._doAllUpgrades()
        # The user folder has now been replaced, so we need to login again.
        self.login('root')
        
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
                