# HOC_VoteAnalyzer

Run download_commons_votes.py to download all available House of Commons (HOC) votes and store them in the folder "csv_files". This is a quite inefficient script and it will put out a lot of warnings/errors. Every vote file in the HOC repository has an index. At the moment the script just tries all indices between 0 and 800. Some indices apear not to be online. In those cases an error is produced.

TODO: modify the script it only downloads the files that are not allready in csv_files

make_dashboard.py runs the network analysis and sets up a server in localhost. The IP-adress of this localhost will appear in the command line.

