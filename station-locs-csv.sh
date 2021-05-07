#!/bin/bash
FILE=$(ls -Art logs | grep station-locations | tail -n 1)
echo "${FILE}"
cp logs/${FILE} .
sed 's/ : /,/g' ${FILE} > tmp
mv tmp ${FILE}
sed 's/:/,/g' ${FILE} > tmp
mv tmp ${FILE}
cp ${FILE} ~/Dropbox\ \(Personal\)/Public/station-locations-latest.csv
rm ${FILE}
