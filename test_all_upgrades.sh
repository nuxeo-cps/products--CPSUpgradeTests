#/bin/sh

until [ -a 'bin/zopectl' ]; do 
  cd ..
done

COMMAND=$(pwd)/bin/zopectl

cd Products/CPSUpgradeTests/tests

for DIR in cps* ; do
 LOGFILE=log.$DIR
 echo "=============================================="
 echo Running tests for $DIR
 echo Logging into $(pwd)/$LOGFILE
 $COMMAND test --dir Products/CPSUpgradeTests --tests-pattern $DIR &> $LOGFILE
 cat $LOGFILE | grep Ran
done


