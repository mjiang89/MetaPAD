#include "utils/parameters.h"
#include "utils/commandline_flags.h"
#include "utils/utils.h"
#include "frequent_pattern_mining/frequent_pattern_mining.h"
#include "data/documents.h"
#include "classification/feature_extraction.h"
#include "classification/label_generation.h"
#include "classification/predict_quality.h"
#include "model_training/segmentation.h"

using FrequentPatternMining::Pattern;
using FrequentPatternMining::patterns;

int main(int argc, char* argv[])
{
    parseCommandFlags(argc, argv);

    sscanf(argv[1], "%d", &NTHREADS);
    omp_set_num_threads(NTHREADS);

    // load stopwords, documents, and capital information
    Documents::loadStopwords(STOPWORDS_FILE);
    Documents::loadAllTrainingFiles(TRAIN_FILE, POS_TAGS_FILE, TRAIN_CAPITAL_FILE);
    Documents::splitIntoSentences();

    FrequentPatternMining::mine(MIN_SUP, MAX_LEN);
    // check the patterns
    if (INTERMEDIATE) {
        FILE* out = tryOpen("tmp/frequent_patterns.txt", "w");
        vector<pair<int, int>> order;
        for (int i = 0; i < patterns.size(); ++ i) {
            order.push_back(make_pair(patterns[i].currentFreq, i));
        }
        //sort(order.rbegin(), order.rend());
        for (int iter = 0; iter < order.size(); ++ iter) {
            int i = order[iter].second;
            for (int j = 0; j < patterns[i].tokens.size(); ++ j) {
                fprintf(out, "%d%c", patterns[i].tokens[j], j + 1 == patterns[i].tokens.size() ? '\n' : ' ');
            }
        }
        fclose(out);
    }

    vector<string> featureNames;
    vector<vector<double>> features = Features::extract(featureNames);
    fprintf(stderr, "feature extraction done!\n");

    if (INTERMEDIATE) {
        FILE* out = tryOpen("tmp/features.tsv", "w");
        for (int i = 0; i < features.size(); ++ i) {
            if (features[i].size() > 0) {
                for (int j = 0; j < features[i].size(); ++ j) {
                    fprintf(out, "%.10f%c", features[i][j], j + 1 == features[i].size() ? '\n' : '\t');
                }
            }
        }
        fclose(out);
    }

    vector<Pattern> truth;
    if (LABEL_FILE != "") {
        cerr << "=== Load Existing Labels ===" << endl;
        truth = Label::loadLabels(LABEL_FILE);
    } else {
        // generate labels
        cerr << "=== Generate Labels ===" << endl;
        truth = Label::generate(features, featureNames, ALL_FILE, QUALITY_FILE);
    }
    int recognized = Features::recognize(truth);

    if (INTERMEDIATE) {
        FILE* out = tryOpen("tmp/generated_label.txt", "w");
        for (Pattern pattern : truth) {
            for (int j = 0; j < pattern.tokens.size(); ++ j) {
                fprintf(out, "%d%c", pattern.tokens[j], j + 1 == pattern.tokens.size() ? '\n' : ' ');
            }
        }
        fclose(out);

        out = tryOpen("tmp/features_for_labels.tsv", "w");
        for (Pattern pattern : truth) {
            int i = FrequentPatternMining::pattern2id[pattern.hashValue];
            if (features[i].size() > 0) {
                for (int j = 0; j < features[i].size(); ++ j) {
                    fprintf(out, "%.10f%c", features[i][j], j + 1 == features[i].size() ? '\n' : '\t');
                }
            }
        }
        fclose(out);
    }

    // SegPhrase, +, ++, +++, ...
    if (ENABLE_POS_TAGGING) {
        Segmentation::initializePosTags(Documents::posTag2id.size());
    }
    for (int iteration = 0; iteration < ITERATIONS; ++ iteration) {
        fprintf(stderr, "Feature Matrix = %d X %d\n", features.size(), features.back().size());
        predictQuality(patterns, features, featureNames);
        cerr << "prediction done" << endl;

        // check the quality
        if (INTERMEDIATE) {
            char filename[256];
            sprintf(filename, "tmp/quality_patterns_iter_%d.txt", iteration);
            FILE* out = tryOpen(filename, "w");
            vector<pair<double, int>> order;
            for (int i = 0; i < patterns.size(); ++ i) {
                if (patterns[i].size() > 1 && patterns[i].currentFreq > 0) {
                    order.push_back(make_pair(patterns[i].quality, i));
                }
            }
            sort(order.rbegin(), order.rend());
            for (int iter = 0; iter < order.size(); ++ iter) {
                int i = order[iter].second;
                fprintf(out, "%.10f\t", patterns[i].quality);
                for (int j = 0; j < patterns[i].tokens.size(); ++ j) {
                    fprintf(out, "%d%c", patterns[i].tokens[j], j + 1 == patterns[i].tokens.size() ? '\n' : ' ');
                }
            }
        }

        constructTrie(); // update the current frequent enough patterns
        if (!ENABLE_POS_TAGGING) {
            cerr << "[Length Penalty Mode]" << endl;
            double penalty = EPS;
            if (true) {
                // Binary Search for Length Penalty
                double lower = EPS, upper = 200;
                for (int _ = 0; _ < 10; ++ _) {
                    penalty = (lower + upper) / 2;
                    //cerr << "iteration " << _ << ": " << penalty << endl;
                    Segmentation segmentation(penalty);
                    segmentation.train(Documents::sentences);
                    double wrong = 0, total = 0;
                    # pragma omp parallel for reduction (+:total,wrong)
                    for (int i = 0; i < truth.size(); ++ i) {
                        if (truth[i].label == 1) {
                            ++ total;
                            vector<double> f;
                            vector<int> pre;
                            segmentation.viterbi(truth[i].tokens, f, pre);
                            wrong += pre[truth[i].tokens.size()] != 0;
                        }
                    }
                    if (wrong / total <= DISCARD) {
                        lower = penalty;
                    } else {
                        upper = penalty;
                    }
                }
                cerr << "Length Penalty = " << penalty << endl;
            }
            // Running Segmentation
            Segmentation segmentation(penalty);
            segmentation.train(Documents::sentences);
            // Recompute & Augment Features
            Features::augment(features, segmentation, featureNames);
        } else {
            cerr << "[POS Tags Mode]" << endl;
            if (true) {
                Segmentation segmentation(ENABLE_POS_TAGGING);
                double last = 1e100;
                for (int inner = 0; inner < 10; ++ inner) {
                    double energy = segmentation.adjustPOS(Documents::sentences, MIN_SUP);
                    if (fabs(energy - last) / fabs(last) < EPS) {
                        break;
                    }
                    last = energy;
                }
            }

            if (INTERMEDIATE) {
                char filename[256];
                sprintf(filename, "tmp/pos_tags_iter_%d.txt", iteration);
                FILE* out = tryOpen(filename, "w");
                for (int i = 0; i < Documents::posTag.size(); ++ i) {
                    fprintf(out, "\t%s", Documents::posTag[i].c_str());
                }
                fprintf(out, "\n");
                for (int i = 0; i < Documents::posTag.size(); ++ i) {
                    fprintf(out, "%s", Documents::posTag[i].c_str());
                    for (int j = 0; j < Documents::posTag.size(); ++ j) {
                        fprintf(out, "\t%.10f", Segmentation::connect[i][j]);
                    }
                    fprintf(out, "\n");
                }
                fclose(out);
            }

            Segmentation segmentation(ENABLE_POS_TAGGING);
            segmentation.trainPOS(Documents::sentences, MIN_SUP);
            // Recompute & Augment Features
            Features::augment(features, segmentation, featureNames);
        }

        // check the quality
        if (INTERMEDIATE) {
            char filename[256];
            sprintf(filename, "tmp/frequent_quality_patterns_iter_%d.txt", iteration);
            FILE* out = tryOpen(filename, "w");
            vector<pair<double, int>> order;
            for (int i = 0; i < patterns.size(); ++ i) {
                if (patterns[i].size() > 1 && patterns[i].currentFreq > 0) {
                    order.push_back(make_pair(patterns[i].quality, i));
                }
            }
            sort(order.rbegin(), order.rend());
            for (int iter = 0; iter < order.size(); ++ iter) {
                int i = order[iter].second;
                fprintf(out, "%.10f\t", patterns[i].quality);
                for (int j = 0; j < patterns[i].tokens.size(); ++ j) {
                    fprintf(out, "%d%c", patterns[i].tokens[j], j + 1 == patterns[i].tokens.size() ? '\n' : ' ');
                }
            }
        }

        if (INTERMEDIATE) {
            char filename[256];
            sprintf(filename, "tmp/augmented_features_for_labels_%d.tsv", iteration);
            FILE* out = tryOpen(filename, "w");
            for (Pattern pattern : truth) {
                int i = FrequentPatternMining::pattern2id[pattern.hashValue];
                if (features[i].size() > 0) {
                    for (int j = 0; j < features[i].size(); ++ j) {
                        fprintf(out, "%.10f%c", features[i][j], j + 1 == features[i].size() ? '\n' : '\t');
                    }
                }
            }
            fclose(out);
        }
    }

    if (true) {
        FILE* out = tryOpen("tmp/quality_phrases.txt", "w");
        vector<pair<double, int>> order;
        for (int i = 0; i < patterns.size(); ++ i) {
            if (patterns[i].size() > 1 && patterns[i].currentFreq > 0) {
                order.push_back(make_pair(patterns[i].quality, i));
            }
        }
        sort(order.rbegin(), order.rend());
        for (int iter = 0; iter < order.size(); ++ iter) {
            int i = order[iter].second;
            fprintf(out, "%.10f\t", patterns[i].quality);
            for (int j = 0; j < patterns[i].tokens.size(); ++ j) {
                fprintf(out, "%d%c", patterns[i].tokens[j], j + 1 == patterns[i].tokens.size() ? '\n' : ' ');
            }
        }
    }

    return 0;
}
