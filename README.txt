CPSUpgradeTests
===============

This is a product that contains tests to upgrade from several different
CPS versions to the latest CPS version.

Usage
-----

Install this product in the Products directory of your CPS installation.
Run the tests with Products/CPSUpgradeTests/run_upgrade_tests

You can also run each test separately with
bin/zopectl test --dir Products/CPSUpgradeTests --tests-pattern test_cpsxyz

Where you replace xyz with the CPS version, for example 324 or 335.


Extending the existing tests with new product tests
---------------------------------------------------


Creating a test for a new CPS Version
-------------------------------------

- In CPSUpgradeTests/tests create a new subfolder named cpsxyz, where xyz
  is the version number, for example cps340 for CPS 3.4.0.
  
- Copy the custom_zodb.py from cps324 to the new folder.

- Copy the test that most resembles the test you want to do to test_cpsxyz.py.

- Modify test_cpsxyz.py to fit your test:

  - You need to change the db_dir class attribute to cpsxyz. 
  
  - You need to make sure your testing subclass is the correct one for this
    test. There are currently one testing subclass, but there will be more
    in the near future:
    
    - PreGenericSetupTestCase: Should work with all CPS versions before 3.4.
      
      This test case will create a portal_setup tool, run all available
      upgrades, install first the CPSDefault:default profile, and then
      install all extension profiles. After each profile installation, it
      will also again run any available upgrades (there may be new ones
      available after installing a profile).
  
  - You may also need to change or modify the test method itself, to test the
    things that are actally upgraded. To be able to reuse the test code, the
    test method mostly calls only other methods. The first of this method is
    self._upgrade(), and the following ones are methods that tests that the
    upgrade worked. A typical example of the test method is:
     
    def test_upgrade(self):
        self._upgrade()
        self._verifyDocument()
        self._verifyPublishing()
        self._verifyCalendaring()
     
    You can typically only have one test method per test, as each test method
    will use the same database. 

- Create a new empty Zope instance (or at least delete the ZODB in the 
  instance you use). Call the initial user "manager" with password "manager".
  Install the CPS ver sion you want to upgrade from. Make sure all CPS
  products you want to test are installed in the Products directory. For
  standard CPS, this should be a full CPS installation. (Known as CPS-full in
  CPS <= 3.3.8 and CPS + CPSGroupWare in CPS >= 3.4.0)
  
  If you want to test upgrades of customer products or projects the tests
  shold not be a part of CPSUpgradeTests, although you can of course base
  the tests on this product. But the tests here should only include standard
  CPS products.
  
- Create a CPS site, called cps. Call the manager user "manager" (default)
  and use "manager" as the password. 
  
- Run the installation for all the products you have. CPS 3.2 and 3.3 typically
  installs all products you have, but in 3.4 you need to install each profile
  separately.
  
- Open the /cps/logged_in URL, to create the home area with calendar and such.

- Now, create content. Any product that is installed and have upgrades should
  have something to upgrade. Some tests that the content has been upgraded
  should also be made. For most standard CPS products there are test methods
  on the base test case (UpgradeTestCase). The list of content that has to be
  created to use these tests are listed in the cps_content_list.txt file.
  
  A good procedure here is to add the content for one product, then copy the
  Data.fs to the new testing instance and run the test. If they work, continue
  with the next product until finished.

- Lastly, when all the tests are running, purge the databse and copy the purged
  database into the test directory. No need to have a bigger database than 
  necessary. 
  

How it works
------------

In each database directory, there is a file called "custom_zodb.py". This file
will throuhg t