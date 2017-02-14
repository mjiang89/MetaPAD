#ifndef __SEGMENTATION_H__
#define __SEGMENTATION_H__

#include <cassert>

#include "../utils/utils.h"
#include "../frequent_pattern_mining/frequent_pattern_mining.h"
using FrequentPatternMining::Pattern;
// === global variables ===
using FrequentPatternMining::patterns;
using FrequentPatternMining::pattern2id;
using FrequentPatternMining::id2ends;

mutex POSTagMutex[SUFFIX_MASK + 1];

struct TrieNode {
    unordered_map<TOTAL_TOKENS_TYPE, size_t> children;

    PATTERN_ID_TYPE id;

    TrieNode() {
        id = -1;
        children.clear();
    }
};
vector<TrieNode> trie;

// ===

void constructTrie() {
    trie.clear();
    trie.push_back(TrieNode());
    for (int i = 0; i < patterns.size(); ++ i) {
        const vector<TOTAL_TOKENS_TYPE>& tokens = patterns[i].tokens;
        if (tokens.size() == 0 || tokens.size() > 1 && patterns[i].currentFreq == 0) {
            continue;
        }
        size_t u = 0;
        for (const TOTAL_TOKENS_TYPE& token : tokens) {
            if (!trie[u].children.count(token)) {
                trie[u].children[token] = trie.size();
                trie.push_back(TrieNode());
            }
            u = trie[u].children[token];
        }
        trie[u].id = i;
    }
    cerr << "# of trie nodes = " << trie.size() << endl;
}

class Segmentation
{
private:
    static const double INF;
    static vector<vector<TOTAL_TOKENS_TYPE>> total;

public:
    static vector<vector<double>> connect, disconnect;

    static void initializePosTags(int n) {
        // uniformly initialize
        connect.resize(n);
        for (int i = 0; i < n; ++ i) {
            connect[i].resize(n);
            for (int j = 0; j < n; ++ j) {
                connect[i][j] = 1.0 / n;
            }
        }
        getDisconnect();
        total = vector<vector<TOTAL_TOKENS_TYPE>>(connect.size(), vector<TOTAL_TOKENS_TYPE>(connect.size(), 0));
        for (TOTAL_TOKENS_TYPE i = 1; i < Documents::totalWordTokens; ++ i) {
            if (!Documents::isEndOfSentence(i - 1)) {
                ++ total[Documents::posTags[i - 1]][Documents::posTags[i]];
            }
        }
    }

    static void getDisconnect() {
        disconnect = connect;
        for (int i = 0; i < connect.size(); ++ i) {
            for (int j = 0; j < connect[i].size(); ++ j) {
                disconnect[i][j] = 1 - connect[i][j];
            }
        }
    }

    static void normalizePosTags() {
        for (int i = 0; i < connect.size(); ++ i) {
            double sum = 0;
            for (int j = 0; j < connect[i].size(); ++ j) {
                sum += connect[i][j];
            }
            if (sum > EPS) {
                for (int j = 0; j < connect[i].size(); ++ j) {
                    connect[i][j] /= sum;
                }
            } else {
                for (int j = 0; j < connect[i].size(); ++ j) {
                    connect[i][j] = 1.0 / (double)connect[i].size();
                }
            }
        }
        getDisconnect();
    }

    static void logPosTags() {
        for (int i = 0; i < connect.size(); ++ i) {
            for (int j = 0; j < connect[i].size(); ++ j) {
                connect[i][j] = log(connect[i][j] + EPS);
                disconnect[i][j] = log(disconnect[i][j] + EPS);
            }
        }
    }
private:
    double penalty;
    bool ENABLE_POS_TAGGING;
    double *prob, *quality;

    // generated
    int maxLen;

    void normalize() {
        vector<double> sum(maxLen + 1, 0);
        for (PATTERN_ID_TYPE i = 0; i < patterns.size(); ++ i) {
            sum[patterns[i].size()] += prob[i];
        }
        for (PATTERN_ID_TYPE i = 0; i < patterns.size(); ++ i) {
            prob[i] /= sum[patterns[i].size()];
        }
    }

    void initialize() {
        // compute maximum tokens
        maxLen = 0;
        for (int i = 0; i < patterns.size(); ++ i) {
            maxLen = max(maxLen, patterns[i].size());
        }

        prob = new double[patterns.size()];
        quality = new double[patterns.size()];
        for (PATTERN_ID_TYPE i = 0; i < patterns.size(); ++ i) {
            prob[i] = quality[i] = 0;
        }
        for (PATTERN_ID_TYPE i = 0; i < patterns.size(); ++ i) {
            prob[i] = patterns[i].currentFreq;
        }
        normalize();
    }

public:

    double getProb(int id) const {
        return exp(prob[id]);
    }

    ~Segmentation() {
        delete [] prob;
        delete [] quality;
    }

    Segmentation(bool ENABLE_POS_TAGGING) : ENABLE_POS_TAGGING(ENABLE_POS_TAGGING) {
        initialize();
        for (int i = 0; i < patterns.size(); ++ i) {
            prob[i] = log(prob[i] + EPS);
            if (patterns[i].size() > 1) {
                prob[i] += log(patterns[i].quality + EPS);
            }
        }
    }

    Segmentation(double penalty) : penalty(penalty) {
        initialize();
        // P(length)
        vector<double> pLen(maxLen + 1, 1);
        double total = 1;
        for (int i = 1; i <= maxLen; ++ i) {
            pLen[i] = pLen[i - 1] / penalty;
            total += pLen[i];
        }
        for (int i = 0; i <= maxLen; ++ i) {
            pLen[i] /= total;
        }

        for (int i = 0; i < patterns.size(); ++ i) {
            prob[i] = log(prob[i] + EPS) + log(pLen[patterns[i].size() - 1]);
            if (patterns[i].size() > 1) {
                prob[i] += log(patterns[i].quality + EPS);
            }
        }
    }

    inline double viterbi(const vector<TOKEN_ID_TYPE> &tokens, vector<double> &f, vector<int> &pre) {
        f.clear();
        f.resize(tokens.size() + 1, -INF);
        pre.clear();
        pre.resize(tokens.size() + 1, -1);
        f[0] = 0;
        pre[0] = 0;
        for (size_t i = 0 ; i < tokens.size(); ++ i) {
            if (f[i] < -1e80) {
                continue;
            }
            for (size_t j = i, u = 0; j < tokens.size(); ++ j) {
                if (!trie[u].children.count(tokens[j])) {
                    break;
                }
                u = trie[u].children[tokens[j]];
                if (trie[u].id != -1) {
                    PATTERN_ID_TYPE id = trie[u].id;
                    double p = prob[id];
                    if (f[i] + p > f[j + 1]) {
                        f[j + 1] = f[i] + p;
                        pre[j + 1] = i;
                    }
                }
            }
        }
        return f[tokens.size()];
    }

    inline double viterbi_proba(const vector<TOKEN_ID_TYPE> &tokens, vector<double> &f, vector<int> &pre) {
        f.clear();
        f.resize(tokens.size() + 1, 0);
        pre.clear();
        pre.resize(tokens.size() + 1, -1);
        f[0] = 1;
        pre[0] = 0;
        for (size_t i = 0 ; i < tokens.size(); ++ i) {
            Pattern pattern;
            for (size_t j = i, u = 0; j < tokens.size(); ++ j) {
                if (!trie[u].children.count(tokens[j])) {
                    break;
                }
                u = trie[u].children[tokens[j]];
                if (trie[u].id != -1 && j - i + 1 != tokens.size()) {
                    PATTERN_ID_TYPE id = trie[u].id;
                    double p = exp(prob[id]);
                    if (f[i] * p > f[j + 1]) {
                        f[j + 1] = f[i] * p;
                        pre[j + 1] = i;
                    }
                }
            }
        }
        return f[tokens.size()];
    }

    inline double viterbi(const vector<TOKEN_ID_TYPE> &tokens, const vector<POS_ID_TYPE> &tags, vector<double> &f, vector<int> &pre) {
        f.clear();
        f.resize(tokens.size() + 1, -INF);
        pre.clear();
        pre.resize(tokens.size() + 1, -1);
        f[0] = 0;
        pre[0] = 0;
        for (size_t i = 0 ; i < tokens.size(); ++ i) {
            if (f[i] < -1e80) {
                continue;
            }
            Pattern pattern;
            double cost = 0;
            for (size_t j = i, u = 0; j < tokens.size(); ++ j) {
                if (!trie[u].children.count(tokens[j])) {
                    break;
                }
                u = trie[u].children[tokens[j]];
                if (trie[u].id != -1) {
                    PATTERN_ID_TYPE id = trie[u].id;
                    double p = cost + prob[id];
                    if (f[i] + p + (j + 1 < tokens.size() ? disconnect[tags[j]][tags[j + 1]] : 0) > f[j + 1]) {
                        f[j + 1] = f[i] + p + (j + 1 < tokens.size() ? disconnect[tags[j]][tags[j + 1]] : 0);
                        pre[j + 1] = i;
                    }
                }
                if (j + 1 < tags.size()) {
                    cost += connect[tags[j]][tags[j + 1]];
                }
            }
        }
        return f[tokens.size()];
    }

    inline double viterbi_proba_randomPOS(const vector<TOKEN_ID_TYPE> &tokens, vector<double> &f, vector<int> &pre) {
        Pattern pattern;
        for (int i = 0; i < tokens.size(); ++ i) {
            pattern.append(tokens[i]);
        }
        assert(pattern2id.count(pattern.hashValue));
        PATTERN_ID_TYPE id = pattern2id[pattern.hashValue];

        double sum = 0;
        map<vector<POS_ID_TYPE>, double> memo;
        for (TOTAL_TOKENS_TYPE ed : id2ends[id]) {
            TOTAL_TOKENS_TYPE st = ed - pattern.size() + 1;
            vector<POS_ID_TYPE> tags;
            for (int i = st; i <= ed; ++ i) {
                tags.push_back(Documents::posTags[i]);
            }
            if (memo.count(tags)) {
                sum += memo[tags];
                continue;
            }
            f.clear();
            f.resize(tokens.size() + 1, 0);
            pre.clear();
            pre.resize(tokens.size() + 1, -1);
            f[0] = 1;
            pre[0] = 0;
            for (size_t i = 0 ; i < tokens.size(); ++ i) {
                double cost = 1;
                for (size_t j = i, u = 0; j < tokens.size() && j - i + 1 < tokens.size(); ++ j) {
                    if (!trie[u].children.count(tokens[j])) {
                        assert(j != i);
                        break;
                    }
                    u = trie[u].children[tokens[j]];
                    if (trie[u].id != -1) {
                        PATTERN_ID_TYPE id = trie[u].id;
                        double p = cost * exp(prob[id]);
                        if (f[i] * p * (j + 1 < tokens.size() ? disconnect[tags[j]][tags[j + 1]] : 1) > f[j + 1]) {
                            f[j + 1] = f[i] * p * (j + 1 < tokens.size() ? disconnect[tags[j]][tags[j + 1]] : 1);
                            pre[j + 1] = i;
                        }
                    }
                    if (j + 1 < tags.size()) {
                        cost *= connect[tags[j]][tags[j + 1]];
                    }
                }
            }
            memo[tags] = f[tokens.size()];
            sum += f[tokens.size()];
        }
        return sum / id2ends[id].size();
    }

    inline void train(vector<pair<TOTAL_TOKENS_TYPE, TOTAL_TOKENS_TYPE>> &sentences) {
        for (PATTERN_ID_TYPE i = 0; i < patterns.size(); ++ i) {
            patterns[i].currentFreq = 0;
            id2ends[i].clear();
        }

        double energy = 0;
        # pragma omp parallel for reduction(+:energy) schedule(dynamic, SENTENCE_CHUNK_SIZE)
        for (INDEX_TYPE senID = 0; senID < sentences.size(); ++ senID) {
            vector<TOKEN_ID_TYPE> tokens;
            for (TOTAL_TOKENS_TYPE i = sentences[senID].first; i <= sentences[senID].second; ++ i) {
                tokens.push_back(Documents::wordTokens[i]);
            }
            vector<double> f;
            vector<int> pre;

            double bestExplain = viterbi(tokens, f, pre);

            int i = (int)tokens.size();
            assert(f[i] > -1e80);
            energy += f[i];
    		while (i > 0) {
    			int j = pre[i];
                size_t u = 0;
                for (int k = j; k < i; ++ k) {
                    assert(trie[u].children.count(tokens[k]));
                    u = trie[u].children[tokens[k]];
                }
                if (trie[u].id != -1) {
                    PATTERN_ID_TYPE id = trie[u].id;
                    separateMutex[id & SUFFIX_MASK].lock();
                    ++ patterns[id].currentFreq;
                    if (i - j > 1) {
                        id2ends[id].push_back(sentences[senID].first + i - 1);
                    }
                    separateMutex[id & SUFFIX_MASK].unlock();
                }
    			i = j;
    		}
        }
        //cerr << "Energy = " << energy << endl;
    }

    inline double trainPOS(vector<pair<TOTAL_TOKENS_TYPE, TOTAL_TOKENS_TYPE>> &sentences, int MIN_SUP) {
        for (PATTERN_ID_TYPE i = 0; i < patterns.size(); ++ i) {
            patterns[i].lastFreq = patterns[i].currentFreq;
            patterns[i].currentFreq = 0;
            id2ends[i].clear();
        }

        vector<vector<double>> backup = connect;
        logPosTags();

        double energy = 0;
        //FILE* out = fopen("tmp/xxx", "w");
        # pragma omp parallel for reduction(+:energy) schedule(dynamic, SENTENCE_CHUNK_SIZE)
        for (INDEX_TYPE senID = 0; senID < sentences.size(); ++ senID) {
            vector<TOKEN_ID_TYPE> tokens;
            vector<POS_ID_TYPE> tags;
            for (TOTAL_TOKENS_TYPE i = sentences[senID].first; i <= sentences[senID].second; ++ i) {
                tokens.push_back(Documents::wordTokens[i]);
                tags.push_back(Documents::posTags[i]);
            }
            vector<double> f;
            vector<int> pre;

            double bestExplain = viterbi(tokens, tags, f, pre);

            int i = (int)tokens.size();
            assert(f[i] > -1e80);
            energy += f[i];
    		while (i > 0) {
    			int j = pre[i];
                size_t u = 0;
                for (int k = j; k < i; ++ k) {
                    assert(trie[u].children.count(tokens[k]));
                    u = trie[u].children[tokens[k]];
                }
                if (trie[u].id != -1) {
                    PATTERN_ID_TYPE id = trie[u].id;
                    separateMutex[id & SUFFIX_MASK].lock();
                    ++ patterns[id].currentFreq;
                    if (i - j > 1) {
                        id2ends[id].push_back(sentences[senID].first + i - 1);
                    }
                    separateMutex[id & SUFFIX_MASK].unlock();
                }
    			i = j;
    		}
        }
        connect = backup;
        getDisconnect();

        cerr << "Energy = " << energy << endl;
        return energy;
    }

    inline double adjustPOS(vector<pair<TOTAL_TOKENS_TYPE, TOTAL_TOKENS_TYPE>> &sentences, int MIN_SUP) {
        for (PATTERN_ID_TYPE i = 0; i < patterns.size(); ++ i) {
            patterns[i].lastFreq = patterns[i].currentFreq;
            patterns[i].currentFreq = 0;
        }

        vector<vector<TOTAL_TOKENS_TYPE>> cnt(connect.size(), vector<TOTAL_TOKENS_TYPE>(connect.size(), 0));
        logPosTags();

        double energy = 0;
        //FILE* out = fopen("tmp/xxx", "w");
        # pragma omp parallel for reduction(+:energy) schedule(dynamic, SENTENCE_CHUNK_SIZE)
        for (INDEX_TYPE senID = 0; senID < sentences.size(); ++ senID) {
            vector<TOKEN_ID_TYPE> tokens;
            vector<POS_ID_TYPE> tags;
            for (TOTAL_TOKENS_TYPE i = sentences[senID].first; i <= sentences[senID].second; ++ i) {
                tokens.push_back(Documents::wordTokens[i]);
                tags.push_back(Documents::posTags[i]);
            }
            vector<double> f;
            vector<int> pre;

            double bestExplain = viterbi(tokens, tags, f, pre);

            int i = (int)tokens.size();
            assert(f[i] > -1e80);
            energy += f[i];
    		while (i > 0) {
    			int j = pre[i];
                size_t u = 0;
                for (int k = j; k < i; ++ k) {
                    assert(trie[u].children.count(tokens[k]));
                    u = trie[u].children[tokens[k]];
                }
                if (trie[u].id != -1) {
                    PATTERN_ID_TYPE id = trie[u].id;
                    separateMutex[id & SUFFIX_MASK].lock();
                    ++ patterns[id].currentFreq;
                    separateMutex[id & SUFFIX_MASK].unlock();

                    if (patterns[id].lastFreq >= MIN_SUP) {
                        for (int k = j + 1; k < i; ++ k) {
                            int index = tags[k] * cnt.size() + tags[k - 1];
                            POSTagMutex[index & SUFFIX_MASK].lock();
                            ++ cnt[tags[k - 1]][tags[k]];
                            POSTagMutex[index & SUFFIX_MASK].unlock();
                        }
                    }
                }
    			i = j;
    		}
        }

        for (int i = 0; i < connect.size(); ++ i) {
            for (int j = 0; j < connect[i].size(); ++ j) {
                if (total[i][j] > 0) {
                    connect[i][j] = (double)cnt[i][j] / total[i][j];
                } else {
                    connect[i][j] = 0;
                }
            }
        }
        getDisconnect();
        cerr << "Energy = " << energy << endl;
        return energy;
    }
};

const double Segmentation::INF = 1e100;
vector<vector<double>> Segmentation::connect;
vector<vector<double>> Segmentation::disconnect;
vector<vector<TOTAL_TOKENS_TYPE>> Segmentation::total;
#endif
