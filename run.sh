rm -r output *.pyc
cd cseg
make clean
rm -r tmp results
cd ..

mkdir output
cd cseg
make all
mkdir tmp results
cd ..

python metapad.py encrypt output/top-encrypted.txt output/top-label.txt output/top-positive.txt output/top-key.txt data/corpus.txt data/goodpattern.txt data/stopwords.txt TOP
python metapad.py encrypt output/bottom-encrypted.txt output/bottom-label.txt output/bottom-positive.txt output/bottom-key.txt data/corpus.txt data/goodpattern.txt data/stopwords.txt BOTTOM

python metapad.py encryptFast output/top-token-train.txt output/top-token-mapping.txt output/top-token-casesen.txt output/top-token-quality.txt data/corpus.txt data/goodpattern.txt TOP
python metapad.py encryptFast output/bottom-token-train.txt output/bottom-token-mapping.txt output/bottom-token-casesen.txt output/bottom-token-quality.txt data/corpus.txt data/goodpattern.txt BOTTOM

cp output/top-token-train.txt cseg/tmp/tokenized_train.txt
cp output/top-token-mapping.txt cseg/tmp/token_mapping.txt
cp output/top-token-casesen.txt cseg/tmp/case_tokenized_train.txt
cp output/top-token-quality.txt cseg/tmp/tokenized_all.txt
cp output/top-token-quality.txt cseg/tmp/tokenized_quality.txt
cd cseg
java -jar Tokenizer.jar -m test -i ../data/stopwords.txt -o tmp/tokenized_stopwords.txt -t tmp/token_mapping.txt -c N -thread 15
./bin/segphrase_train --verbose --thread 15 --max_len 20
cd ..
cp cseg/tmp/quality_phrases.txt output/top-token-phrase.txt

cp output/bottom-token-train.txt cseg/tmp/tokenized_train.txt
cp output/bottom-token-mapping.txt cseg/tmp/token_mapping.txt
cp output/bottom-token-casesen.txt cseg/tmp/case_tokenized_train.txt
cp output/bottom-token-quality.txt cseg/tmp/tokenized_all.txt
cp output/bottom-token-quality.txt cseg/tmp/tokenized_quality.txt
cd cseg
java -jar Tokenizer.jar -m test -i ../data/stopwords.txt -o tmp/tokenized_stopwords.txt -t tmp/token_mapping.txt -c N -thread 15
./bin/segphrase_train --verbose --thread 15 --max_len 20
cd ..
cp cseg/tmp/quality_phrases.txt output/bottom-token-phrase.txt

python metapad.py salientFast output/top-salient.csv output/top-key.txt output/top-token-phrase.txt output/top-token-mapping.txt
python metapad.py salientFast output/bottom-salient.csv output/bottom-key.txt output/bottom-token-phrase.txt output/bottom-token-mapping.txt

python metapad.py mptable output/top-table.txt output/top-metapattern.txt output/top-salient.csv output/top-key.txt data/corpus.txt data/goodclass.txt data/verbs.txt data/stopwords.txt TOP
python metapad.py mptable output/bottom-table.txt output/bottom-metapattern.txt output/bottom-salient.csv output/bottom-key.txt data/corpus.txt data/goodclass.txt data/verbs.txt data/stopwords.txt BOTTOM

python metapad.py synonym output/top-synonym.txt output/top-table.txt data/goodclass.txt data/verbs.txt data/stopwords.txt
python metapad.py synonym output/bottom-synonym.txt output/bottom-table.txt data/goodclass.txt data/verbs.txt data/stopwords.txt

python metapad.py topdown output/topdown-table.txt output/top-table.txt output/top-synonym.txt data/goodclass.txt data/stopwords.txt 0.1 0.8
python metapad.py bottomup output/bottomup-table.txt output/bottom-table.txt output/bottom-synonym.txt data/goodclass.txt data/stopwords.txt 0.1 0.8

python metapad.py attribute output/attribute-topdown.txt output/topdown-table.txt data/goodclass.txt data/verbs.txt data/stopwords.txt 5
python metapad.py attribute output/attribute-bottomup.txt output/bottomup-table.txt data/goodclass.txt data/verbs.txt data/stopwords.txt 5

python metapad.py result output/result-topdown.txt output/attribute-topdown.txt MAX MAX MAX
python metapad.py result output/result-bottomup.txt output/attribute-bottomup.txt MAX MAX MAX

