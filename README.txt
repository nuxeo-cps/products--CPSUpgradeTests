CPSUpgradeTests
===============

This is a product that contains tests to upgrade from several different
CPS versions to the latest CPS version.

Usage
-----

Install this product in the Products directory of your CPS installation.
Run the tests with Products/CPSUpgradeTests/run_upgrade_tests.sh

You can also run each test separately with
bin/zopectl test --dir Products/CPSUpgradeTests --tests-pattern 123

Where you replace 123 with the CPS version, for example 324 or 335.


Extending the existing tests with new product tests
---------------------------------------------------

The tests are all located in files called test_cps123.py, where 123 is the
version number being tested, for example 338 for CPS 3.3.8. However, all these
tests do is call methods on the base test case classes. It first calls
_upgrade(), which performs the actual upgrade. This method comes either from
upgradetestcase.PreGenericTestCase or upgradetestcase.PostGenericTestCase.

Next it verifies that the upgrade has worked correctly by calling a set of
_verify*() methods, all defined on upgradetestcase.UpgradeTestCase. 

These are the steps to add the test for a product:

 - Make a new instance of Zope with the correct CPS version installed.
   CPS v 1.2.3 to follow the standard example. ;-)

 - Copy over the Data.fs from the right folder, in this case
   CPSUpgradeTests/tests/cps123 to the var directory of your new Zope 
   instance, and start the server. 

 - Log in with manager/manager and go to the CPS instance. Make sure your
   product is installed, and create the content or setup that needs upgrade.
   
 - Pack the database, exit the server and copy the modified Data.fs back
   to CPSUpgradeTests/tests/cps123.

 - Add a method on upgradetestcase.UpgradeTestCase, named _verifySomething(),
   that verifies that the upgrade has worked.
   
 - Add the _verifySomething() method to the test method in the test, in 
   this case test_cps123.py. 
   
 - Run the test. Fix the test, or the setup of the objects, or the upgrade
   until it it works.

 - Repeat with next CPS version until all valid CPS versions are done.


Creating a test for a new CPS Version
-------------------------------------

- In CPSUpgradeTests/tests create a new subfolder named cps123, where 123
  is the version number, for example cps340 for CPS 3.4.0.
  
- Copy the custom_zodb.py from cps324 to the new folder.

- Copy the test that most resembles the test you want to do to test_cps123.py.

- Modify test_cps123.py to fit your test:
  
  - You need to change the DB_NAME "constant" defined in the beginning of
    the file to cps123. 
  
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

When running ZopeTestCases they will look for a file name "custom_zodb.py" in
the directory specified as the testinghome attribute on the configuration.
When importing the Testing module, it will set the tetsinghome attribute to
it's own directory, and the custom_zodb.py in lib/python/Testing will be used.
This specifies the use of an empty "DemoStorage", which is a temporrary
in-memory storage.

However, we want to override this and use our own databases. Therefore, the
start of every test_123.py file starts with importing Testing, and then
overriding the testinghome attribute. This way each test can use it's own
Data.fs. The custom_zodb.py that is located in each cps123 directory will also
wrap the Data.fs in a DemoStorage, so that changes is never written to disk.

However, since this database setup is done only once, and there seems to be no
good way of tearing it down, it means that we can only run one test at a time, 
since every test needs its own database.

Therefore, the base UpgradeTestCase will in beforeSetup() check that the right
database is running, to avoid a lot of false failures. 
Running "bin/zopectl test --dir Products/CPSUpgradeTests" will therefore give
you error messages like this:

"This test was run with the wrong database! Please make sure that you run the
tests with the test_all_upgrades script."

To avoid that, you specify which test you want to run, with --tests-pattern 123,
where 123 as usual is the CPS version.

  bin/zopectl test --dir Products/CPSUpgradeTests --tests-pattern 338

This will run only the upgrade from version 3.3.8. You can of course also
run all the upgrade tests at once, with the run_all_upgrades.sh script.

