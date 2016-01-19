#!/bin/bash

for FILE in *
do 
echo $FILE
git add $FILE
git commit -m "Ajout de $FILE"
done
