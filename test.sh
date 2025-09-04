in_dir=$1

counter=1
for i in `ls $in_dir*Season*.csv`
do
    echo "Processing File $i"
    NAME=`basename $i .csv`
    ./etsy.sh $i $in_dir$NAME
done

