find . -type f | while read FILE ; do
    newfile="$(echo ${FILE} | sed -E 's|^./([^0-9X]*)-([0-9X]*)(.*)$|\2-\1\3|')" ;
    mv "${FILE}" "${newfile}" ;
done 