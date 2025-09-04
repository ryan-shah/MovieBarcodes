in_dir=$1
out_dir=$2
out_name=$3

for i in `ls $in_dir | grep .csv`
do
  filename=$(basename "$i" .jpg.csv)
#   ./mov-bar.py -i $in_dir$i -o $out_dir$out_name$filename-long.jpg -l 16 -w 2
  ./etsy.sh $in_dir$i $out_dir$out_name$filename 
done