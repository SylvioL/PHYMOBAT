#!/bin/bash

for FILE in *
do 
echo $FILE
git add -f $FILE
git commit -m "Modification de $FILE"
done
