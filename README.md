# daisy-extract
This Python script will take a DAISY talking book, scan its metadata, and then extract all of the audio content into a friendlier structure.

- By default the book will be placed in the directory `<output>\<author>\<title>` (where `<output>` is the output path specified on the command line)
- The MP3 files will be numbered and renamed to reflect their true contents
- A playlist will be created to play the entire book

Note: This script has only been tested with books which follow the DAISY 2.02 standard, designated as "Full audio with NCC only".

## How do I use it?
When I get around to it, I'll package the script so it will be installable with pip and runnable from anywhere.  But for now, to get set up:

1. Install Python and pip.  I've only tested it with Python 3.4 so far.
2. In a directory of your choice, run:
```
git clone https://github.com/jscholes/daisy-extract
cd daisy-extract
pip install -r requirements.txt
```
Alternatively you can download the contents of the repository as a ZIP file, extract it somewhere, and execute the two last commands above without cloning from Git.
3. Run the script by typing:

    python extract.py

which will show you the possible command line options.

Feel free to submit pull requests or file bugs here on GitHub.