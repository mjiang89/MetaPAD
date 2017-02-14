__author__ = 'mengjiang'

from sys import *
from utils import *
from random import randint

def Encrypt(file_output_encrypted,file_output_label,file_output_positive,file_output_key,file_input_entitylinking,file_input_goodpattern,file_input_stopwords,NEGATIVE,LEVEL):
	stopwordset = SetFromFile(file_input_stopwords)
	key2value = {}
	value_int = 1000000
	fw = open(file_output_encrypted,'w')
	fr = open(file_input_entitylinking,'rb')
	for line in fr:
		xml = line.strip('\r\n')
		sentence = XMLToSentence(xml)
		n = len(sentence)
		if sentence[n-1][0] == 'PERIOD': sentence = sentence[0:n-1]
		text = ''
		for [classname,words] in sentence:
			if classname == '':
				word = words
				if word.lower() in stopwordset:
					text += ' '+word
				else:
					key = '\t'+word
					if not key in key2value:
						value = ''
						for c in str(value_int):
							value += chr(ord('a')+int(c))
						key2value[key] = value
						value_int += 1
					text += ' '+key2value[key]
			else:
				if LEVEL == 'TOP':
					if '.' in classname:  # TOP - begin
						pos = classname.find('.')
						classname = classname[0:pos] # TOP - end
				key = classname+'\t'
				if not key in key2value:
					value = ''
					for c in str(value_int):
						value += chr(ord('a')+int(c))
					key2value[key] = value
					value_int += 1
				text += ' '+key2value[key]
		if len(text) > 0:
			fw.write(text[1:]+'\n')
	fr.close()
	fw.close()
	labelset = set()
	fr = open(file_input_goodpattern,'rb')
	for line in fr:
		xml = line.strip('\r\n')
		sentence = XMLToSentence(xml)
		text = ''
		for [classname,words] in sentence:
			if classname == '':
				word = words
				if word.lower() in stopwordset:
					text += ' '+word
				else:
					key = '\t'+word
					if not key in key2value:
						value = ''
						for c in str(value_int):
							value += chr(ord('a')+int(c))
						key2value[key] = value
						value_int += 1
					text += ' '+key2value[key]
			else:
				if LEVEL == 'TOP':
					if '.' in classname: # TOP - begin
						pos = classname.find('.')
						classname = classname[0:pos] # TOP - end
				key = classname+'\t'
				if not key in key2value:
					value = ''
					for c in str(value_int):
						value += chr(ord('a')+int(c))
					key2value[key] = value
					value_int += 1
				text += ' '+key2value[key]
		if len(text) > 0:
			labelset.add(text[1:])
	fr.close()
	fw = open(file_output_label,'w')
	fw_positive = open(file_output_positive,'w')
	labels = sorted(labelset)
	n_label = len(labels)
	for label in labels:
		fw.write(label+'\t1\n')
		fw_positive.write(label+'\n')
	wordgroups = []
	for label in labels:
		wordgroups.append(label.split(' '))
	for i in range(0,n_label*NEGATIVE):
		k = randint(0,n_label-1)
		l = len(wordgroups[k])
		p = randint(0,l-1)
		q = randint(0,l-1)
		xmin,xmax = min(p,q),max(p,q)
		if xmin == xmax: continue
		label = ''
		for j in range(xmin,xmax+1):
			label += ' '+wordgroups[k][j]
		label = label[1:]
		if label in labelset: continue
		fw.write(label+'\t0\n')
		labelset.add(label)
	fw_positive.close()
	fw.close()
	fw = open(file_output_key,'w')
	for [key,value] in sorted(key2value.items(),key=lambda x:x[1]):
		fw.write(value+'\t'+key+'\n')
	fw.close()

def IsVerb(word,verbset):
	if word in verbset: return True
	l = len(word)
	if l > 3 and word[l-3:] == 'ing': return True
	if l > 2 and word[l-2:] == 'ed': return True
	if l > 2 and word[l-2:] == 'ly': return True 
	if l > 2 and word[l-2:] == 'es' and (word[0:l-2] in verbset or word[0:l-1] in verbset): return True
	if l > 2 and word[l-1] == 's' and word[0:l-1] in verbset: return True
	return False

def MPTable(file_output_table,file_output_metapattern,file_input_salient,file_input_key,file_input_entitylinking,file_input_goodclass,file_input_verbs,file_input_stopwords,LEVEL):
	goodclassset = SetFromFile(file_input_goodclass,False)
	verbset = SetFromFile(file_input_verbs)
	stopwordset = SetFromFile(file_input_stopwords)
	stopwordpatternset = set(['and','or','say','says','said','told','announced'])
	commaset = set([':','-','.',';'])
	key2value = {}
	fr = open(file_input_key,'rb')
	for line in fr:
		arr = line.strip('\r\n').split('\t')
		key,classname = arr[0],arr[1]
		value = ''
		if classname == '' or classname == 'PERIOD':
			value = arr[2]
		else:
			value = '<'+arr[1]+'>'+arr[2]+'</'+arr[1]+'>'
		key2value[key] = value
	fr.close()
	pattern2score = {}
	fr = open(file_input_salient,'rb')
	for line in fr:
		arr = line.strip('\r\n').split(',')
		pattern = ''
		for key in arr[0].split('_'):
			if key in key2value:
				pattern += ' '+key2value[key]
			else:
				pattern += ' '+key
		pattern = pattern[1:]
		if pattern == '': continue
		if 'that' in pattern or ' , and ' in pattern or ' , or ' in pattern: continue
		score = float(arr[1])
		sentence = XMLToSentence(pattern)
		n = len(sentence)
		posStart,posEnd = -1,-1
		for i in range(0,n):
			[classname,words] = sentence[i]
			if not (classname == '' and (words == ',' or words in commaset or words.lower() in stopwordset or words.lower() in stopwordpatternset)):
				posStart = i
				break
		for j in range(n-1,-1,-1): 
			[classname,words] = sentence[j]
			if not (classname == '' and (words == '(' or words in commaset or words.lower() in stopwordset or words.lower() in stopwordpatternset)):
				posEnd = j
				break
		if posStart < 0 or posEnd < 0 or posStart >= posEnd:
			continue
		sentence = sentence[posStart:posEnd+1]
		n = len(sentence)
		[classname,words] = sentence[0]
		if classname == '' and IsVerb(words.lower(),verbset):
			continue
		[classname,words] = sentence[n-1]
		if classname == '' and IsVerb(words.lower(),verbset):
			continue
		mention_class_set = set()
		num_mention_context = 0
		for [classname,words] in sentence:
			rootclass = classname
			if '.' in classname:
				pos = classname.find('.')
				rootclass = classname[0:pos]
			if rootclass in goodclassset:
				mention_class_set.add(classname)
			elif not (classname == '' and (len(words) == 1 or words.lower() in stopwordset)):
				num_mention_context += 1
		num_mention_class = len(mention_class_set)
		if num_mention_class == 0: continue
		if not ((num_mention_class > 1 and num_mention_context == 0) or (num_mention_context > 0)): continue
		pattern = SentenceToXML(sentence)
		if pattern in pattern2score:
			score = max(score,pattern2score[pattern])
		pattern2score[pattern] = score
	fr.close()
	fw = open(file_output_metapattern,'w')
	for [pattern,score] in sorted(pattern2score.items(),key=lambda x:-x[1]):
		sentence = XMLToSentence(pattern)
		dollar = SentenceToDollar(sentence)
		fw.write(pattern+'\t'+str(score)+'\t'+dollar+'\n')
	fw.close()
	index = PatternIndex(file_output_metapattern)
	n_index = len(index)
	fw = open(file_output_table,'w')
	fw.write('MENTION\tXMLBOTTOM\tXML\tPATTERN\tSCORE\tPOS\n')
	mention = 0
	fr = open(file_input_entitylinking,'rb')
	for line in fr:
		xml = line.strip('\r\n')
		sentence_bottom = XMLToSentence(xml)
		if LEVEL == 'TOP':
			sentence = [] # TOP - begin
			for [classname,words] in sentence_bottom:
				if '.' in classname:
					pos = classname.find('.')
					rootclass = classname[0:pos]
					sentence.append([rootclass,words])
				else:
					sentence.append([classname,words]) # TOP - end
		else:
			sentence = sentence_bottom # BOTTOM
		keys = SentenceToKeys(sentence)
		n = len(sentence)
		for i in range(0,n):
			[classname,words] = sentence[i]
			rootclass = classname
			if '.' in classname:
				pos = classname.find('.')
				rootclass = classname[0:pos]
			if not rootclass in goodclassset: continue
			mention += 1
			entity = ''
			for word in words: entity += ' '+word
			entity = entity[1:]
			last_end = -1			
			for p in range(max(0,i-n_index+1),i+1):
				max_score,max_s,max_end = 0,'',-1
				for j in range(min(n_index,n-i),max(1,i-p),-1):
					temp = index[j-1]
					k = 0
					while k < j:
						key = keys[p+k]
						if not key in temp:
							break
						temp = temp[key]
						k += 1
					if k == j:
						[pattern,score] = temp
						if score < max_score: continue
						max_score = score
						xml_bottom = SentenceToXML(sentence_bottom[p:p+j])
						xml = SentenceToXML(sentence[p:p+j])
						s = str(mention)+'\t'+xml_bottom+'\t'+xml+'\t'+pattern+'\t'+str(score)+'\t'+str(i-p)
						max_s = s
						max_end = p+j
				if max_score > 0 and max_end > last_end:
					last_end = max_end
					fw.write(max_s+'\n')
	fr.close()
	fw.close()

def Synonym(file_output_synonym,file_input_table,file_input_goodclass,file_input_verbs,file_input_stopwords):
	goodclassset = SetFromFile(file_input_goodclass,False)
	verbset = SetFromFile(file_input_verbs)
	stopwordset = SetFromFile(file_input_stopwords)
	patterns = []
	pattern2patternid = {}
	str_goodclass2patternidset = {}
	goodclass_entity2patternidset = {}
	invalidpatternset = set()
	fr = open(file_input_table,'rb')
	fr.readline()
	for line in fr:
		arr = line.strip('\r\n').split('\t')
		pattern = arr[3]
		if pattern in invalidpatternset: continue
		if not pattern in pattern2patternid:
			patternid = len(patterns)
			sentence = XMLToSentence(pattern)
			n = len(sentence)
			pos_goodclass,pos_otherclass = [],[]
			for pos in range(0,n):
				[classname,words] = sentence[pos]
				if classname == '' or classname == 'PERIOD': continue
				rootclass = classname
				if '.' in classname:
					_pos = classname.find('.')
					rootclass = classname[0:_pos]
				if rootclass in goodclassset:
					pos_goodclass.append([pos,classname])
				else:
					pos_otherclass.append(pos)
			if len(pos_goodclass)+len(pos_otherclass) < 2:
				invalidpatternset.add(pattern)
				continue
			str_goodclass = ''
			for [pos,classname] in sorted(pos_goodclass,key=lambda x:x[1]):
				str_goodclass += '\t'+classname
			str_goodclass = str_goodclass[1:]
			patterns.append([pattern,0,pos_goodclass,pos_otherclass,str_goodclass,{}])
			if not str_goodclass in str_goodclass2patternidset:
				str_goodclass2patternidset[str_goodclass] = set()
			str_goodclass2patternidset[str_goodclass].add(patternid)
			pattern2patternid[pattern] = patternid
		patternid = pattern2patternid[pattern]
		patterns[patternid][1] += 1
		xml = arr[2]
		sentence = XMLToSentence(xml)
		n = len(sentence)
		pos_goodclass = patterns[patternid][2]
		pos_otherclass = patterns[patternid][3]
		entities = ['' for i in range(0,n)]
		for [pos,classname] in pos_goodclass:
			words = sentence[pos][1]
			entity = ''
			for word in words:
				entity += ' '+word
			entity = entity[1:]
			entities[pos] = entity
		for pos in pos_otherclass:
			[classname,words] = sentence[pos]
			entity = ''
			for word in words:
				entity += ' '+word
			entity = entity[1:]
			entities[pos] = entity
		n_goodclass = len(pos_goodclass)
		for i in range(0,n_goodclass):
			[pos,classname] = pos_goodclass[i]
			goodclass_entity = classname+'\t'+entities[pos]
			values = []
			for j in range(0,n_goodclass):
				if i == j: continue
				pos = pos_goodclass[j][0]
				values.append(entities[pos])
			for pos in pos_otherclass:
				values.append(entities[pos])
			instance = ''
			for value in sorted(values):
				instance += '\t'+value
			instance = instance[1:]
			if not goodclass_entity in patterns[patternid][5]:
				patterns[patternid][5][goodclass_entity] = set()
			patterns[patternid][5][goodclass_entity].add(instance)
			if not goodclass_entity in goodclass_entity2patternidset:
				goodclass_entity2patternidset[goodclass_entity] = set()
			goodclass_entity2patternidset[goodclass_entity].add(patternid)
	fr.close()
	fw = open(file_output_synonym,'w')
	for [pattern,count,pos_goodclass,pos_otherclass,str_goodclass,goodclass_entity2instanceset] in sorted(patterns,key=lambda x:-x[1]):
		otherpattern2scores = {}
		for patternid in str_goodclass2patternidset[str_goodclass]:
			otherpattern = patterns[patternid][0]
			othergoodclass_entity2instanceset = patterns[patternid][5]
			if otherpattern == pattern: continue
			otherpattern2scores[otherpattern] = [0.0,0.0]
			sum_n1,sum_n2,sum_n3 = 0,0,0
			for goodclass_entity in goodclass_entity2instanceset:
				if not goodclass_entity in othergoodclass_entity2instanceset: continue
				instanceset = goodclass_entity2instanceset[goodclass_entity]
				otherinstanceset = othergoodclass_entity2instanceset[goodclass_entity]
				n1,n2,n3 = len(instanceset),len(otherinstanceset),len(instanceset & otherinstanceset)
				sum_n1 += n1
				sum_n2 += n2
				sum_n3 += n3
			if not sum_n3 == 0:
				otherpattern2scores[otherpattern][0] = 1.0*sum_n3/sum_n1
				otherpattern2scores[otherpattern][1] = 1.0*sum_n3/sum_n2
		for [otherpattern,[score,recall]] in sorted(otherpattern2scores.items(),key=lambda x:-x[1][0]):
			if score == 0: break
			fw.write(pattern+'\t'+otherpattern+'\t'+str(score)+'\t'+str(recall)+'\n')
	goodclass_attributename2patterns = {}
	for pattern in invalidpatternset:
		sentence = XMLToSentence(pattern)
		goodclass = ''
		attributes = []
		for [classname,words] in sentence:
			if classname == '' or classname == 'PERIOD':
				word = words.lower()
				if not (len(word) == 1 or word in stopwordset or IsVerb(word,verbset)):
					attributes.append(word)
			else:
				rootclass = classname
				if '.' in classname:
					_pos = classname.find('.')
					rootclass = classname[0:_pos]
				if rootclass in goodclassset: goodclass = classname
		if goodclass == '' or len(attributes) == 0: continue
		attributename = ''
		for attribute in attributes: attributename += '\t'+attribute
		goodclass_attributename = goodclass+'\t'+attributename[1:]
		if not goodclass_attributename in goodclass_attributename2patterns:
			goodclass_attributename2patterns[goodclass_attributename] = []
		goodclass_attributename2patterns[goodclass_attributename].append(pattern)
	for [goodclass_attributename,patterns] in goodclass_attributename2patterns.items():
		n = len(patterns)
		if n < 2: continue
		for i in range(0,n):
			for j in range(0,n):
				if i == j: continue
				fw.write(patterns[i]+'\t'+patterns[j]+'\t-1\t-1\n')
	fw.close()

def GetSynonym(file_input_synonym_input,file_input_goodclass,file_input_stopwords):
	if file_input_synonym_input == 'NULL':
		return {}
	goodclassset = SetFromFile(file_input_goodclass,False)
	stopwordset = SetFromFile(file_input_stopwords)
	scores_all,scores_contextual = [],[]
	recalls_all,recalls_contextual = [],[]
	pattern2attributeset = {}
	fr = open(file_input_synonym,'rb')
	for line in fr:
		arr = line.strip('\r\n').split('\t')
		score,recall = float(arr[2]),float(arr[3])
		if score < 0: continue
		scores_all.append(score)
		recalls_all.append(recall)
		pattern = arr[0]
		if pattern in pattern2attributeset:
			attributeset_left = pattern2attributeset[pattern]
		else:
			sentence = XMLToSentence(pattern)
			attributeset_left = set()
			for [classname,words] in sentence:
				if classname == '' or classname == 'PERIOD':
					word = words.lower()
					if len(word) == 1 or word in stopwordset: continue
					attributeset_left.add(word)
			pattern2attributeset[pattern] = attributeset_left
		pattern = arr[1]
		if pattern in pattern2attributeset:
			attributeset_right = pattern2attributeset[pattern]
		else:
			sentence = XMLToSentence(pattern)
			attributeset_right = set()
			for [classname,words] in sentence:
				if classname == '':
					word = words.lower()
					if len(word) == 1 or word in stopwordset: continue
					attributeset_right.add(word)
			pattern2attributeset[pattern] = attributeset_right
		n = len(attributeset_left & attributeset_right)
		if n == 0: continue
		scores_contextual.append(score)
		recalls_contextual.append(recall)
	fr.close()
	threshold_score,threshold_recall = 0.0,0.0
	if len(scores_contextual) > 0:
		threshold_score = 1.0*sum(scores_contextual)/len(scores_contextual)
	if len(recalls_contextual) > 0:
		threshold_recall = 1.0*sum(recalls_contextual)/len(recalls_contextual)
	pattern2synonyms = {}
	fr = open(file_input_synonym,'rb')
	for line in fr:
		arr = line.strip('\r\n').split('\t')
		score,recall = float(arr[2]),float(arr[3])
		if score < 0 or (score >= threshold_score and recall >= threshold_recall):
			pattern,synonym = arr[0],arr[1]
			if not pattern in pattern2synonyms:
				pattern2synonyms[pattern] = []
			pattern2synonyms[pattern].append(synonym)
	fr.close()
	return pattern2synonyms

def TopDown(file_output_table,file_input_table,file_input_synonym,file_input_goodclass,file_input_stopwords,PARA_ALPHA,PARA_GAMMA):
	goodclassset = SetFromFile(file_input_goodclass,False)
	pattern2synonyms = GetSynonym(file_input_synonym,file_input_goodclass,file_input_stopwords)
	pattern2rootclass2pos2classname2entity2count = {}
	fr = open(file_input_table,'rb')
	fr.readline()
	for line in fr:
		arr = line.strip('\r\n').split('\t')
		xml,pattern = arr[1],arr[3]
		sentence = XMLToSentence(xml)
		n = len(sentence)
		for pos in range(0,n):
			[classname,words] = sentence[pos]
			if classname == '' or classname == 'PERIOD': continue
			rootclass = classname
			if '.' in classname:
				_pos = classname.find('.')
				rootclass = classname[0:_pos]
			if not rootclass in goodclassset: continue	
			entity = ''
			for word in words:
				entity += ' '+word
			entity = entity[1:]
			if not pattern in pattern2rootclass2pos2classname2entity2count:
				pattern2rootclass2pos2classname2entity2count[pattern] = {}
			if not rootclass in pattern2rootclass2pos2classname2entity2count[pattern]:
				pattern2rootclass2pos2classname2entity2count[pattern][rootclass] = {}
			if not pos in pattern2rootclass2pos2classname2entity2count[pattern][rootclass]:
				pattern2rootclass2pos2classname2entity2count[pattern][rootclass][pos] = {}
			if not classname in pattern2rootclass2pos2classname2entity2count[pattern][rootclass][pos]:
				pattern2rootclass2pos2classname2entity2count[pattern][rootclass][pos][classname] = {}
			if not entity in pattern2rootclass2pos2classname2entity2count[pattern][rootclass][pos][classname]:
				pattern2rootclass2pos2classname2entity2count[pattern][rootclass][pos][classname][entity] = 0
			pattern2rootclass2pos2classname2entity2count[pattern][rootclass][pos][classname][entity] += 1
	fr.close()
	pattern2pos2classname_level = {}
	for [pattern,rootclass2pos2classname2entity2count] in pattern2rootclass2pos2classname2entity2count.items():
		pattern2pos2classname_level[pattern] = {}
		for [rootclass,pos2classname2entity2count] in rootclass2pos2classname2entity2count.items():
			for [pos,classname2entity2count] in pos2classname2entity2count.items():
				classname2entity2countAll = {}
				for [classname,entity2count] in classname2entity2count.items():
					for [entity,count] in entity2count.items():
						if not classname in classname2entity2countAll:
							classname2entity2countAll[classname] = {}
						if not entity in classname2entity2countAll[classname]:
							classname2entity2countAll[classname][entity] = 0
						classname2entity2countAll[classname][entity] += count
				if pattern in pattern2synonyms:
					for synonym in pattern2synonyms[pattern]:
						if not synonym in pattern2rootclass2pos2classname2entity2count: continue
						if not rootclass in pattern2rootclass2pos2classname2entity2count[synonym]: continue
						pos2classname2entity2count_synonym = pattern2rootclass2pos2classname2entity2count[synonym][rootclass]
						for [pos_synonym,classname2entity2count_synonym] in pos2classname2entity2count_synonym.items():
							for [classname,entity2count] in classname2entity2count_synonym.items():
								for [entity,count] in entity2count.items():
									if not classname in classname2entity2countAll:
										classname2entity2countAll[classname] = {}
									if not entity in classname2entity2countAll[classname]:
										classname2entity2countAll[classname][entity] = 0
									classname2entity2countAll[classname][entity] += count
				classname2counts,parent2children,rootclassset = {},{},set()
				for [classname,entity2count] in classname2entity2countAll.items():
					n1,n2 = 0,0
					for [entiy,count] in entity2count.items():
						n1 += 1
						n2 += count
					while '.' in classname:
						_pos = classname.rfind('.')
						if not classname in classname2counts:
							classname2counts[classname] = [0,0]
						classname2counts[classname][0] += n1
						classname2counts[classname][1] += n2
						child,parent = classname,classname[0:_pos]
						if not parent in parent2children:
							parent2children[parent] = set()
						parent2children[parent].add(child)
						classname = parent
					if not classname in classname2counts:
						classname2counts[classname] = [0,0]
					classname2counts[classname][0] += n1
					classname2counts[classname][1] += n2
					rootclassset.add(classname)
				classname_level = []
				for rootclass in rootclassset:
					parentclasses = []
					parentclasses.append(rootclass)
					while not len(parentclasses) == 0:
						parent = parentclasses.pop(0)
						if parent in parent2children:
							parentcounts = classname2counts[parent]
							sumcounts = [0,0]
							maxcounts = [0,0]
							for child in parent2children[parent]:
								childcounts = classname2counts[child]
								sumcounts = [sumcounts[i]+childcounts[i] for i in range(0,2)]
								maxcounts = [max(maxcounts[i],childcounts[i]) for i in range(0,2)]
							parentcounts_only = [parentcounts[i]-sumcounts[i] for i in range(0,2)]
							maxcounts = [max(maxcounts[i],parentcounts_only[i]) for i in range(0,2)]
							gammas = [1.0*sumcounts[i]/parentcounts[i] for i in range(0,2)]
							if gammas[0] >= PARA_GAMMA or gammas[1] >= PARA_GAMMA:
								for child in parent2children[parent]:
									childcounts = classname2counts[child]
									alphas = [1.0*childcounts[i]/maxcounts[i] for i in range(0,2)]
									if alphas[0] >= PARA_ALPHA or alphas[1] >= PARA_ALPHA:
										parentclasses.append(child)
								alphas = [1.0*parentcounts_only[i]/maxcounts[i] for i in range(0,2)]
								if alphas[0] >= PARA_ALPHA or alphas[1] >= PARA_ALPHA:
									level = parent.count('.')
									classname_level.append([parent,level])
							else:
								level = parent.count('.')
								classname_level.append([parent,level])
						else:
							level = parent.count('.')
							classname_level.append([parent,level])
				pattern2pos2classname_level[pattern][pos] = sorted(classname_level,key=lambda x:-x[1])
	fw = open(file_output_table,'w')
	fr = open(file_input_table,'rb')
	line = fr.readline()
	fw.write(line.strip('\r\n')+'\n')
	for line in fr:
		arr = line.strip('\r\n').split('\t')
		pattern = arr[3]
		sentence_xmlbottom = XMLToSentence(arr[1])
		sentence_xml = XMLToSentence(arr[2])
		sentence_pattern = XMLToSentence(arr[3])
		if pattern in pattern2pos2classname_level:
			for [pos,classname_level] in pattern2pos2classname_level[pattern].items():
				bottomclass = sentence_xmlbottom[pos][0]
				best_classname = bottomclass
				for [classname,level] in classname_level:
					if classname in bottomclass:
						best_classname = classname
						break
				sentence_xml[pos][0] = best_classname
				sentence_pattern[pos][0] = best_classname
		xml = SentenceToXML(sentence_xml)
		pattern = SentenceToXML(sentence_pattern)
		fw.write(arr[0]+'\t'+arr[1]+'\t'+xml+'\t'+pattern+'\t'+arr[4]+'\t'+arr[5]+'\n')
	fw.close()

def BottomUp(file_output_table,file_input_table,file_input_synonym,file_input_goodclass,file_input_stopwords,PARA_ALPHA,PARA_GAMMA):
	goodclassset = SetFromFile(file_input_goodclass,False)
	pattern2synonyms = GetSynonym(file_input_synonym,file_input_goodclass,file_input_stopwords)
	pattern2patternformat = {}
	patternformat2pos2classname2entity2count = {}
	fr = open(file_input_table,'rb')
	fr.readline()
	for line in fr:
		arr = line.strip('\r\n').split('\t')
		xml,pattern = arr[2],arr[3]
		sentence_xml = XMLToSentence(xml)
		sentence_pattern = XMLToSentence(pattern)
		n = len(sentence_xml)
		pos_classname_entity = []
		for pos in range(0,n):
			[classname,words] = sentence_xml[pos]
			if classname == '' or classname == 'PERIOD': continue
			rootclass = classname
			if '.' in classname:
				_pos = classname.find('.')
				rootclass = classname[0:_pos]
			if not rootclass in goodclassset: continue
			entity = ''
			for word in words:
				entity += ' '+word
			entity = entity[1:]
			pos_classname_entity.append([pos,classname,entity])
			sentence_pattern[pos][0] = 'NULL'
		patternformat = ''
		if pattern in pattern2patternformat:
			patternformat = pattern2patternformat[pattern]
		else:
			patternformat = SentenceToXML(sentence_pattern)
			pattern2patternformat[pattern] = patternformat
		if not patternformat in patternformat2pos2classname2entity2count:
			patternformat2pos2classname2entity2count[patternformat] = {}
		for [pos,classname,entity] in pos_classname_entity:
			if not pos in patternformat2pos2classname2entity2count[patternformat]:
				patternformat2pos2classname2entity2count[patternformat][pos] = {}
			if not classname in patternformat2pos2classname2entity2count[patternformat][pos]:
				patternformat2pos2classname2entity2count[patternformat][pos][classname] = {}
			if not entity in patternformat2pos2classname2entity2count[patternformat][pos][classname]:
				patternformat2pos2classname2entity2count[patternformat][pos][classname][entity] = 0
			patternformat2pos2classname2entity2count[patternformat][pos][classname][entity] += 1
	fr.close()
	patternformat2pos2classname_level = {}
	for [patternformat,pos2classname2entity2count] in patternformat2pos2classname2entity2count.items():
		patternformat2pos2classname_level[patternformat] = {}
		for [pos,classname2entity2count] in pos2classname2entity2count.items():
			classname2counts,parent2children,rootclassset = {},{},set()
			for [classname,entity2count] in classname2entity2count.items():
				n1,n2 = 0,0
				for [entiy,count] in entity2count.items():
					n1 += 1
					n2 += count
				while '.' in classname:
					_pos = classname.rfind('.')
					if not classname in classname2counts:
						classname2counts[classname] = [0,0]
					classname2counts[classname][0] += n1
					classname2counts[classname][1] += n2
					child,parent = classname,classname[0:_pos]
					if not parent in parent2children:
						parent2children[parent] = set()
					parent2children[parent].add(child)
					classname = parent
				if not classname in classname2counts:
					classname2counts[classname] = [0,0]
				classname2counts[classname][0] += n1
				classname2counts[classname][1] += n2
				rootclassset.add(classname)
			classname_level = []
			for rootclass in rootclassset:
				parentclasses = []
				parentclasses.append(rootclass)
				while not len(parentclasses) == 0:
					parent = parentclasses.pop(0)
					if parent in parent2children:
						parentcounts = classname2counts[parent]
						sumcounts = [0,0]
						maxcounts = [0,0]
						for child in parent2children[parent]:
							childcounts = classname2counts[child]
							sumcounts = [sumcounts[i]+childcounts[i] for i in range(0,2)]
							maxcounts = [max(maxcounts[i],childcounts[i]) for i in range(0,2)]
						parentcounts_only = [parentcounts[i]-sumcounts[i] for i in range(0,2)]
						maxcounts = [max(maxcounts[i],parentcounts_only[i]) for i in range(0,2)]
						gammas = [1.0*sumcounts[i]/parentcounts[i] for i in range(0,2)]
						if gammas[0] >= PARA_GAMMA or gammas[1] >= PARA_GAMMA:
							for child in parent2children[parent]:
								childcounts = classname2counts[child]
								alphas = [1.0*childcounts[i]/maxcounts[i] for i in range(0,2)]
								if alphas[0] >= PARA_ALPHA or alphas[1] >= PARA_ALPHA:
									parentclasses.append(child)
							alphas = [1.0*parentcounts_only[i]/maxcounts[i] for i in range(0,2)]
							if alphas[0] >= PARA_ALPHA or alphas[1] >= PARA_ALPHA:
								level = parent.count('.')
								classname_level.append([parent,level])
						else:
							level = parent.count('.')
							classname_level.append([parent,level])
					else:
						level = parent.count('.')
						classname_level.append([parent,level])
			patternformat2pos2classname_level[patternformat][pos] = sorted(classname_level,key=lambda x:-x[1])
	fw = open(file_output_table,'w')
	fr = open(file_input_table,'rb')
	line = fr.readline()
	fw.write(line.strip('\r\n')+'\n')
	for line in fr:
		arr = line.strip('\r\n').split('\t')
		pattern = arr[3]
		sentence_xmlbottom = XMLToSentence(arr[1])
		sentence_xml = XMLToSentence(arr[2])
		sentence_pattern = XMLToSentence(arr[3])
		if pattern in pattern2patternformat:
			patternformat = pattern2patternformat[pattern]
			if not patternformat in patternformat2pos2classname_level: continue
			for [pos,classname_level] in patternformat2pos2classname_level[patternformat].items():
				bottomclass = sentence_xmlbottom[pos][0]
				best_classname = bottomclass
				for [classname,level] in classname_level:
					if classname in bottomclass:
						best_classname = classname
						break
				sentence_xml[pos][0] = best_classname
				sentence_pattern[pos][0] = best_classname
		xml = SentenceToXML(sentence_xml)
		pattern = SentenceToXML(sentence_pattern)
		fw.write(arr[0]+'\t'+arr[1]+'\t'+xml+'\t'+pattern+'\t'+arr[4]+'\t'+arr[5]+'\n')
	fw.close()

def Attribute(file_output_attribute,file_input_table,file_input_goodclass,file_input_verbs,file_input_stopwords,NUMTOP):
	goodclassset = SetFromFile(file_input_goodclass,False)
	verbset = SetFromFile(file_input_verbs)
	stopwordset = SetFromFile(file_input_stopwords)
	patterns,dollars,pattern2patternid = [],[],{}
	classname2entity_instance2totalcount_attribute_valuetype2count_patternid2count = {}
	fr = open(file_input_table,'rb')
	fr.readline()
	for line in fr:
		arr = line.strip('\r\n').split('\t')
		pattern = arr[3]	
		if not pattern in pattern2patternid:
			patternid = len(patterns)
			patterns.append(pattern)
			dollars.append(SentenceToDollar(XMLToSentence(pattern)))
			pattern2patternid[pattern] = patternid
		patternid = pattern2patternid[pattern]
		xml = arr[2]
		sentence = XMLToSentence(xml)
		n = len(sentence)
		for i in range(0,n):
			[classname,words] = sentence[i]
			rootclass = classname
			if '.' in classname:
				pos = classname.find('.')
				rootclass = classname[0:pos]
			if not rootclass in goodclassset: continue
			classname = '$'+classname
			entity = ''
			for word in words:
				entity += ' '+word
			entity = entity[1:]
			attribute,valuetype_instance = '',[]
			for j in range(i-1,-1,-1):
				[contextclassname,contextwords] = sentence[j]
				if contextclassname == '' or contextclassname == 'PERIOD':
					word = contextwords.lower()
					if not (len(word) == 1 or word in stopwordset or IsVerb(word,verbset)):
						attribute = word+' '+attribute
				else:
					contextualrootclass = contextclassname
					if '.' in contextclassname:
						pos = contextclassname.find('.')
						contextualrootclass = contextclassname[0:pos]
					instance = ''
					for word in contextwords:
						instance += ' '+word
					instance = instance[1:]
					valuetype_instance.append(['$'+contextclassname,instance])
					if contextualrootclass in goodclassset: break
			l = len(attribute)
			if l == 0:
				attribute = 'NULL'
			else:
				attribute = attribute[0:l-1]
			valuetype,instance = '',''
			for [_valuetype,_instance] in sorted(valuetype_instance,key=lambda x:x[0]):
				valuetype += ' '+_valuetype
				instance += '|'+_instance
			if valuetype == '':
				valuetype,instance = 'NULL','NULL'
			else:
				valuetype = valuetype[1:]
				instance = instance[1:]
			if not (attribute == 'NULL' and valuetype == 'NULL'):
				entity_instance = entity+'\t'+instance
				attribute_valuetype = attribute+'\t'+valuetype
				if not classname in classname2entity_instance2totalcount_attribute_valuetype2count_patternid2count:
					classname2entity_instance2totalcount_attribute_valuetype2count_patternid2count[classname] = {}
				if not entity_instance in classname2entity_instance2totalcount_attribute_valuetype2count_patternid2count[classname]:
					classname2entity_instance2totalcount_attribute_valuetype2count_patternid2count[classname][entity_instance] = [0,{},{}]
				classname2entity_instance2totalcount_attribute_valuetype2count_patternid2count[classname][entity_instance][0] += 1
				if not attribute_valuetype in classname2entity_instance2totalcount_attribute_valuetype2count_patternid2count[classname][entity_instance][1]:
					classname2entity_instance2totalcount_attribute_valuetype2count_patternid2count[classname][entity_instance][1][attribute_valuetype] = 0
				classname2entity_instance2totalcount_attribute_valuetype2count_patternid2count[classname][entity_instance][1][attribute_valuetype] += 1
				if not patternid in classname2entity_instance2totalcount_attribute_valuetype2count_patternid2count[classname][entity_instance][2]:
					classname2entity_instance2totalcount_attribute_valuetype2count_patternid2count[classname][entity_instance][2][patternid] = 0
				classname2entity_instance2totalcount_attribute_valuetype2count_patternid2count[classname][entity_instance][2][patternid] += 1
			attribute,valuetype_instance = '',[]
			for j in range(i+1,n):
				[contextclassname,contextwords] = sentence[j]
				if contextclassname == '' or contextclassname == 'PERIOD':
					word = contextwords.lower()
					if not (len(word) == 1 or word in stopwordset or IsVerb(word,verbset)):
						attribute += ' '+word
				else:
					contextualrootclass = contextclassname
					if '.' in contextclassname:
						pos = contextclassname.find('.')
						contextualrootclass = contextclassname[0:pos]
					instance = ''
					for word in contextwords:
						instance += ' '+word
					instance = instance[1:]
					valuetype_instance.append(['$'+contextclassname,instance])
					if contextualrootclass in goodclassset: break
			l = len(attribute)
			if l == 0:
				attribute = 'NULL'
			else:
				attribute = attribute[1:]
			valuetype,instance = '',''
			for [_valuetype,_instance] in sorted(valuetype_instance,key=lambda x:x[0]):
				valuetype += ' '+_valuetype
				instance += '|'+_instance
			if valuetype == '':
				valuetype,instance = 'NULL','NULL'
			else:
				valuetype = valuetype[1:]
				instance = instance[1:]
			if not (attribute == 'NULL' and valuetype == 'NULL'):
				entity_instance = entity+'\t'+instance
				attribute_valuetype = attribute+'\t'+valuetype
				if not classname in classname2entity_instance2totalcount_attribute_valuetype2count_patternid2count:
					classname2entity_instance2totalcount_attribute_valuetype2count_patternid2count[classname] = {}
				if not entity_instance in classname2entity_instance2totalcount_attribute_valuetype2count_patternid2count[classname]:
					classname2entity_instance2totalcount_attribute_valuetype2count_patternid2count[classname][entity_instance] = [0,{},{}]
				classname2entity_instance2totalcount_attribute_valuetype2count_patternid2count[classname][entity_instance][0] += 1
				if not attribute_valuetype in classname2entity_instance2totalcount_attribute_valuetype2count_patternid2count[classname][entity_instance][1]:
					classname2entity_instance2totalcount_attribute_valuetype2count_patternid2count[classname][entity_instance][1][attribute_valuetype] = 0
				classname2entity_instance2totalcount_attribute_valuetype2count_patternid2count[classname][entity_instance][1][attribute_valuetype] += 1
				if not patternid in classname2entity_instance2totalcount_attribute_valuetype2count_patternid2count[classname][entity_instance][2]:
					classname2entity_instance2totalcount_attribute_valuetype2count_patternid2count[classname][entity_instance][2][patternid] = 0
				classname2entity_instance2totalcount_attribute_valuetype2count_patternid2count[classname][entity_instance][2][patternid] += 1
	fr.close()
	dollarsLower = [dollar.lower() for dollar in dollars]
	fw = open(file_output_attribute,'w')
	fw.write('C\tr_N_T\tn_E_I\tN\tT\tr_E_I\tc_E_I\tE\tI\tn_MP\tMPN\tcMPN\ttopMP\tcTopMP\n')
	for [classname,entity_instance2totalcount_attribute_valuetype2count_patternid2count] in sorted(classname2entity_instance2totalcount_attribute_valuetype2count_patternid2count.items(),key=lambda x:x[0]):
		attributename_valuetype2entity_instance2totalcount_patternid2count = {}
		for entity_instance in entity_instance2totalcount_attribute_valuetype2count_patternid2count:
			[totalcount,attribute_valuetype2count,patternid2count] = entity_instance2totalcount_attribute_valuetype2count_patternid2count[entity_instance]
			best_attributename,best_valuetype = '',''
			for [attribute_valuetype,count] in sorted(attribute_valuetype2count.items(),key=lambda x:-x[1]):
				[attribute,valuetype] = attribute_valuetype.split('\t')
				if not attribute == 'NULL':
					best_attributename = attribute
					best_valuetype = valuetype
					break
				if best_attributename == '':
					best_attributename = attribute
					best_valuetype = valuetype
			attributename_valuetype = best_attributename+'\t'+best_valuetype
			if not attributename_valuetype in attributename_valuetype2entity_instance2totalcount_patternid2count:
				attributename_valuetype2entity_instance2totalcount_patternid2count[attributename_valuetype] = {}
			if not entity_instance in attributename_valuetype2entity_instance2totalcount_patternid2count[attributename_valuetype]:
				attributename_valuetype2entity_instance2totalcount_patternid2count[attributename_valuetype][entity_instance] = [0,{}]
			attributename_valuetype2entity_instance2totalcount_patternid2count[attributename_valuetype][entity_instance][0] += totalcount
			for patternid in patternid2count:
				if not patternid in attributename_valuetype2entity_instance2totalcount_patternid2count[attributename_valuetype][entity_instance][1]:
					attributename_valuetype2entity_instance2totalcount_patternid2count[attributename_valuetype][entity_instance][1][patternid] = 0
				attributename_valuetype2entity_instance2totalcount_patternid2count[attributename_valuetype][entity_instance][1][patternid] += patternid2count[patternid]
		C = classname
		rNT = 0
		for [attributename_valuetype,entity_instance2totalcount_patternid2count] in sorted(attributename_valuetype2entity_instance2totalcount_patternid2count.items(),key=lambda x:-len(x[1])):
			[N,T] = attributename_valuetype.split('\t')
			rNT += 1
			cNT = len(entity_instance2totalcount_patternid2count)
			rEI = 0
			for [entity_instance,[totalcount,patternid2count]] in sorted(entity_instance2totalcount_patternid2count.items(),key=lambda x:-x[1][0]):
				rEI += 1
				cEI = totalcount
				[E,I] = entity_instance.split('\t')
				cMP = len(patternid2count)
				rMP = 0
				topMP = ''
				MPN,cMPN = 'NULL',0
				for [patternid,count] in sorted(patternid2count.items(),key=lambda x:-x[1]):
					rMP += 1
					MP = dollars[patternid]
					cMP = count
					if rMP <= NUMTOP:
						topMP += '\t'+MP+'\t'+str(cMP)
					if MPN == 'NULL' and N in dollarsLower[patternid]:
						MPN,cMPN = MP,cMP
				fw.write(C+'\t'+str(rNT)+'\t'+str(cNT)+'\t'+N+'\t'+T+'\t'+str(rEI)+'\t'+str(cEI) \
					+'\t'+E+'\t'+I+'\t'+str(cMP)+'\t'+MPN+'\t'+str(cMPN)+topMP+'\n')
	fw.close()

def GetBottom(classnames):
	ret = ''
	for classname in classnames.split(' '):
		if classname == '': continue
		if not classname[0] == '$': continue
		classname = classname[1:]
		if '.' in classname:
			pos = classname.rfind('.')
			classname = classname[pos+1:]
		ret += ' $'+classname
	if ret == '': return ''
	return ret[1:]

def Result(file_output_result,file_input_attribute,NUMTOP_ATTRIBUTE_VALUETYPE,NUMTOP_ENTITY_VALUE,NUMTOP_META_PATTERN):
	classname2attributevaluetype2namevalue = {}
	classname2attributevaluetype2valuenull = {}
	classname2attributevaluetype2namenull = {}
	fr = open(file_input_attribute,'rb')
	fr.readline()
	for line in fr:
		arr = line.strip('\r\n').split('\t')
		attribute = arr[3]
		classname = GetBottom(arr[0])
		if classname == '': continue
		valuetype = arr[4]
		if not valuetype == 'NULL':
			valuetype = GetBottom(valuetype)
			if valuetype == '': valuetype = 'NULL'
		if attribute == 'NULL' and valuetype == 'NULL': continue
		attributevaluetype = attribute+'\t'+valuetype
		freq = int(arr[6])
		entity = arr[7]
		value = arr[8]
		entityvalue = entity+'\t'+value
		metapattern2count = {}
		for i in range(12,len(arr),2):
			metapattern = arr[i]
			count = int(arr[i+1])
			if not metapattern in metapattern2count:
				metapattern2count[metapattern] = 0
			metapattern2count[metapattern] += count
		if not attribute == 'NULL' and not valuetype == 'NULL':
			# countvalue
			if not classname in classname2attributevaluetype2namevalue:
				classname2attributevaluetype2namevalue[classname] = {}
			if not attributevaluetype in classname2attributevaluetype2namevalue[classname]:
				classname2attributevaluetype2namevalue[classname][attributevaluetype] = [{},{}]
			if not entityvalue in classname2attributevaluetype2namevalue[classname][attributevaluetype][0]:
				classname2attributevaluetype2namevalue[classname][attributevaluetype][0][entityvalue] = 0
			classname2attributevaluetype2namevalue[classname][attributevaluetype][0][entityvalue] += freq
			for metapattern in metapattern2count:
				if not metapattern in classname2attributevaluetype2namevalue[classname][attributevaluetype][1]:
					classname2attributevaluetype2namevalue[classname][attributevaluetype][1][metapattern] = 0
				classname2attributevaluetype2namevalue[classname][attributevaluetype][1][metapattern] += metapattern2count[metapattern]
		elif valuetype == 'NULL' and not attribute == 'NULL':
			# valuenull
			if not classname in classname2attributevaluetype2valuenull:
				classname2attributevaluetype2valuenull[classname] = {}
			if not attributevaluetype in classname2attributevaluetype2valuenull[classname]:
				classname2attributevaluetype2valuenull[classname][attributevaluetype] = [{},{}]
			if not entityvalue in classname2attributevaluetype2valuenull[classname][attributevaluetype][0]:
				classname2attributevaluetype2valuenull[classname][attributevaluetype][0][entityvalue] = 0
			classname2attributevaluetype2valuenull[classname][attributevaluetype][0][entityvalue] += freq
			for metapattern in metapattern2count:
				if not metapattern in classname2attributevaluetype2valuenull[classname][attributevaluetype][1]:
					classname2attributevaluetype2valuenull[classname][attributevaluetype][1][metapattern] = 0
				classname2attributevaluetype2valuenull[classname][attributevaluetype][1][metapattern] += metapattern2count[metapattern]
		elif attribute == 'NULL' and not valuetype == 'NULL':
			# namenull
			if not classname in classname2attributevaluetype2namenull:
				classname2attributevaluetype2namenull[classname] = {}
			if not attributevaluetype in classname2attributevaluetype2namenull[classname]:
				classname2attributevaluetype2namenull[classname][attributevaluetype] = [{},{}]
			if not entityvalue in classname2attributevaluetype2namenull[classname][attributevaluetype][0]:
				classname2attributevaluetype2namenull[classname][attributevaluetype][0][entityvalue] = 0
			classname2attributevaluetype2namenull[classname][attributevaluetype][0][entityvalue] += freq
			for metapattern in metapattern2count:
				if not metapattern in classname2attributevaluetype2namenull[classname][attributevaluetype][1]:
					classname2attributevaluetype2namenull[classname][attributevaluetype][1][metapattern] = 0
				classname2attributevaluetype2namenull[classname][attributevaluetype][1][metapattern] += metapattern2count[metapattern]
	fr.close()
	fw = open(file_output_result,'w')
	fw.write('(ENTITY,NAME,VALUE)\n')
	for [classname,attributevaluetype2count] in sorted(classname2attributevaluetype2namevalue.items(),key=lambda x:x[0]):
		i0 = 0
		for [attributevaluetype,[entityvalue2freq,metapattern2count]] in sorted(attributevaluetype2count.items(),key=lambda x:-len(x[1][0])):
			i0 += 1
			if (not NUMTOP_ATTRIBUTE_VALUETYPE < 0) and i0 > NUMTOP_ATTRIBUTE_VALUETYPE: break
			fw.write(classname+'\t'+str(i0)+'\t'+attributevaluetype+'\n')
			i1 = 0
			for [entityvalue,freq] in sorted(entityvalue2freq.items(),key=lambda x:-x[1]):
				i1 += 1
				if (not NUMTOP_ENTITY_VALUE < 0) and i1 > NUMTOP_ENTITY_VALUE: break
				fw.write('\tEV'+str(i1)+'\t'+entityvalue+'\n') # +'\t'+str(freq)+'\n')
			i2 = 0
			for [metapattern,count] in sorted(metapattern2count.items(),key=lambda x:-x[1]):
				i2 += 1
				if (not NUMTOP_META_PATTERN < 0) and i2 > NUMTOP_META_PATTERN: break
				fw.write('\tMP'+str(i2)+'\t'+metapattern+'\n') # +'\t'+str(count)+'\n')
	fw.write('\n(ENTITY,NAME,NULL)\n')
	for [classname,attributevaluetype2count] in sorted(classname2attributevaluetype2valuenull.items(),key=lambda x:x[0]):
		i0 = 0
		for [attributevaluetype,[entityvalue2freq,metapattern2count]] in sorted(attributevaluetype2count.items(),key=lambda x:-len(x[1][0])):
			i0 += 1
			if (not NUMTOP_ATTRIBUTE_VALUETYPE < 0) and i0 > NUMTOP_ATTRIBUTE_VALUETYPE: break
			fw.write(classname+'\t'+str(i0)+'\t'+attributevaluetype+'\n')
			i1 = 0
			for [entityvalue,freq] in sorted(entityvalue2freq.items(),key=lambda x:-x[1]):
				i1 += 1
				if (not NUMTOP_ENTITY_VALUE < 0) and i1 > NUMTOP_ENTITY_VALUE: break
				fw.write('\tEV'+str(i1)+'\t'+entityvalue+'\n') # +'\t'+str(freq)+'\n')
			i2 = 0
			for [metapattern,count] in sorted(metapattern2count.items(),key=lambda x:-x[1]):
				i2 += 1
				if (not NUMTOP_META_PATTERN < 0) and i2 > NUMTOP_META_PATTERN: break
				fw.write('\tMP'+str(i2)+'\t'+metapattern+'\n') # +'\t'+str(count)+'\n')
	fw.write('\n(ENTITY,NULL,VALUE)\n')
	for [classname,attributevaluetype2count] in sorted(classname2attributevaluetype2namenull.items(),key=lambda x:x[0]):
		i0 = 0
		for [attributevaluetype,[entityvalue2freq,metapattern2count]] in sorted(attributevaluetype2count.items(),key=lambda x:-len(x[1][0])):
			i0 += 1
			if (not NUMTOP_ATTRIBUTE_VALUETYPE < 0) and i0 > NUMTOP_ATTRIBUTE_VALUETYPE: break
			fw.write(classname+'\t'+str(i0)+'\t'+attributevaluetype+'\n')
			i1 = 0
			for [entityvalue,freq] in sorted(entityvalue2freq.items(),key=lambda x:-x[1]):
				i1 += 1
				if (not NUMTOP_ENTITY_VALUE < 0) and i1 > NUMTOP_ENTITY_VALUE: break
				fw.write('\tEV'+str(i1)+'\t'+entityvalue+'\n') # +'\t'+str(freq)+'\n')
			i2 = 0
			for [metapattern,count] in sorted(metapattern2count.items(),key=lambda x:-x[1]):
				i2 += 1
				if (not NUMTOP_META_PATTERN < 0) and i2 > NUMTOP_META_PATTERN: break
				fw.write('\tMP'+str(i2)+'\t'+metapattern+'\n') # +'\t'+str(count)+'\n')
	fw.close()


def EncryptFast(file_output_train,file_output_mapping,file_output_casesen,file_output_quality,file_input_entitylinking,file_input_goodpattern,LEVEL):
	key2value = {}
	fw = open(file_output_train,'w')
	fw_casesen = open(file_output_casesen,'w')
	fr = open(file_input_entitylinking,'rb')
	for line in fr:
		xml = line.strip('\r\n')
		sentence = XMLToSentence(xml)
		n = len(sentence)
		text = ''
		text_casesen = ''
		for [classname,words] in sentence:
			if classname == '':
				word = words
				key = word
				if not key in key2value:
					value = len(key2value)
					key2value[key] = value
				text += ' '+str(key2value[key])
				text_casesen += '0'
			elif classname == 'PERIOD':
				word = words
				text += ' '+word
				text_casesen += '3'		
			else:
				if LEVEL == 'TOP':
					if '.' in classname:  # TOP - begin
						pos = classname.find('.')
						classname = classname[0:pos] # TOP - end
				key = '$'+classname
				if not key in key2value:
					value = len(key2value)
					key2value[key] = value
				text += ' '+str(key2value[key])
				text_casesen += '1'
		if len(text) > 0:
			fw.write(text[1:]+'\n')
			fw_casesen.write(text_casesen+'\n')
	fr.close()
	fw_casesen.close()
	fw.close()
	fw = open(file_output_quality,'w')
	fr = open(file_input_goodpattern,'rb')
	for line in fr:
		xml = line.strip('\r\n')
		sentence = XMLToSentence(xml)
		n = len(sentence)
		text = ''
		for [classname,words] in sentence:
			if classname == '':
				word = words
				key = word
				if not key in key2value:
					value = len(key2value)
					key2value[key] = value
				text += ' '+str(key2value[key])
			else:
				if LEVEL == 'TOP':
					if '.' in classname:  # TOP - begin
						pos = classname.find('.')
						classname = classname[0:pos] # TOP - end
				key = '$'+classname
				if not key in key2value:
					value = len(key2value)
					key2value[key] = value
				text += ' '+str(key2value[key])
		if len(text) > 0:
			fw.write(text[1:]+'\n')
	fr.close()
	fw.close()
	fw = open(file_output_mapping,'w')
	for [key,value] in key2value.items():
		fw.write(str(value)+'\t'+key+'\n')
	fw.close()

def SalientFast(file_output_salient,file_output_key,file_input_phrase,file_input_mapping):
	fw = open(file_output_key,'w')
	fr = open(file_input_mapping,'rb')
	for line in fr:
		arr = line.strip('\r\n').split('\t')
		key,value = arr[0],arr[1]
		if len(value) > 1 and value[0] == '$':
			fw.write(key+'\t'+value[1:]+'\t'+''+'\n')
		else:
			fw.write(key+'\t'+''+'\t'+value+'\n')
	fr.close()
	fw.close()
	fw = open(file_output_salient,'w')
	fr = open(file_input_phrase,'rb')
	for line in fr:
		arr = line.strip('\r\n').split('\t')
		fw.write(arr[1].replace(' ','_')+','+arr[0]+'\n')
	fr.close()
	fw.close()

if __name__ == '__main__':
	func = argv[1]
	if func == 'encrypt':
		file_output_encrypted = argv[2]
		file_output_label = argv[3]
		file_output_positive = argv[4]
		file_output_key = argv[5]
		file_input_entitylinking = argv[6]
		file_input_goodpattern = argv[7]
		file_input_stopwords = argv[8]
		LEVEL = argv[9]
		Encrypt(file_output_encrypted,file_output_label,file_output_positive,file_output_key,file_input_entitylinking,file_input_goodpattern,file_input_stopwords,10,LEVEL)
	elif func == 'mptable':
		file_output_table = argv[2]
		file_output_metapattern = argv[3]
		file_input_salient = argv[4]
		file_input_key = argv[5]
		file_input_entitylinking = argv[6]
		file_input_goodclass = argv[7]
		file_input_verbs = argv[8]
		file_input_stopwords = argv[9]
		LEVEL = argv[10]
		MPTable(file_output_table,file_output_metapattern,file_input_salient,file_input_key,file_input_entitylinking,file_input_goodclass,file_input_verbs,file_input_stopwords,LEVEL)
	elif func == 'synonym':
		file_output_synonym = argv[2]
		file_input_table = argv[3]
		file_input_goodclass = argv[4]
		file_input_verbs = argv[5]
		file_input_stopwords = argv[6]
		Synonym(file_output_synonym,file_input_table,file_input_goodclass,file_input_verbs,file_input_stopwords)
	elif func == 'topdown':
		file_output_table = argv[2]
		file_input_table = argv[3]
		file_input_synonym = argv[4]
		file_input_goodclass = argv[5]
		file_input_stopwords = argv[6]
		PARA_ALPHA = float(argv[7])
		PARA_GAMMA = float(argv[8])
		TopDown(file_output_table,file_input_table,file_input_synonym,file_input_goodclass,file_input_stopwords,PARA_ALPHA,PARA_GAMMA)
	elif func == 'bottomup':
		file_output_table = argv[2]
		file_input_table = argv[3]
		file_input_synonym = argv[4]
		file_input_goodclass = argv[5]
		file_input_stopwords = argv[6]
		PARA_ALPHA = float(argv[7])
		PARA_GAMMA = float(argv[8])
		BottomUp(file_output_table,file_input_table,file_input_synonym,file_input_goodclass,file_input_stopwords,PARA_ALPHA,PARA_GAMMA)
	elif func == 'attribute':
		file_output_attribute = argv[2]
		file_input_table = argv[3]
		file_input_goodclass = argv[4]
		file_input_verbs = argv[5]
		file_input_stopwords = argv[6]
		NUMTOP = int(argv[7])
		Attribute(file_output_attribute,file_input_table,file_input_goodclass,file_input_verbs,file_input_stopwords,NUMTOP)
	elif func == 'result':
		file_output_result = argv[2]
		file_input_attribute = argv[3]
		NUMTOP_ATTRIBUTE_VALUETYPE = -1
		if argv[4].isdigit(): NUMTOP_ATTRIBUTE_VALUETYPE = int(argv[4])
		NUMTOP_ENTITY_VALUE = -1
		if argv[5].isdigit(): NUMTOP_ENTITY_VALUE = int(argv[5])
		NUMTOP_META_PATTERN = -1
		if argv[6].isdigit(): NUMTOP_META_PATTERN = int(argv[6])
		Result(file_output_result,file_input_attribute,NUMTOP_ATTRIBUTE_VALUETYPE,NUMTOP_ENTITY_VALUE,NUMTOP_META_PATTERN)

	elif func == 'encryptFast':
		file_output_train = argv[2]
		file_output_mapping = argv[3]
		file_output_casesen = argv[4]
		file_output_quality = argv[5]
		file_input_entitylinking = argv[6]
		file_input_goodpattern = argv[7]
		LEVEL = argv[8]
		EncryptFast(file_output_train,file_output_mapping,file_output_casesen,file_output_quality,file_input_entitylinking,file_input_goodpattern,LEVEL)
	elif func == 'salientFast':
		file_output_salient = argv[2]
		file_output_key = argv[3]
		file_input_phrase = argv[4]
		file_input_mapping = argv[5]
		SalientFast(file_output_salient,file_output_key,file_input_phrase,file_input_mapping)


