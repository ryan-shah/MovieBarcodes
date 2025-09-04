echo "Reading from: $1"

if [ -z "$3" ]
    then
        OUTFILE="${1%%.*}-with-name"
        NAME="$2"
    else 
        OUTFILE="$2"
        NAME="$3"
fi

echo "Printing to: $OUTFILE"
echo "Title: $NAME"
echo "10x25"
./mov-bar.py -i $1 -w 10 -l 25 -o $OUTFILE-10x25.jpg -n "$NAME"
echo "12x30"
./mov-bar.py -i $1 -w 12 -l 30 -o $OUTFILE-12x30.jpg -n "$NAME"
echo "12x36"
./mov-bar.py -i $1 -w 12 -l 36 -o $OUTFILE-12x36.jpg -n "$NAME"
echo "16x40"
./mov-bar.py -i $1 -w 16 -l 40 -o $OUTFILE-16x40.jpg -n "$NAME"
echo "Done"
