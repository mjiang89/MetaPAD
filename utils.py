__author__ = 'mengjiang'

def CleanText(text):
	text = text.replace('</',' ').replace('<',' ltlt ').replace('>',' gtgt ')
	text = text.replace(' vs. ',' vs ').replace('etc.','etc')
	text = text.replace("'s "," whosewhat ").replace("'S "," whosewhat ")
	text = text.replace("s' ","s whosewhat ").replace("S' ","S whosewhat ")
	words = text.split(' ')
	text = ''
	for word in words:
		if word == '': continue
		l = len(word)
		if word.count('.') >= 2:
			is_valid = True
			for c in word:
				if c == '.': continue
				if c.isdigit():
					is_valid = False
					break
			if is_valid:
				word = word.replace('.','')
		elif l > 1 and l <= 5 and word[l-1] == '.' and word[0].isalpha() and word[0].isupper():
			word = word[0:l-1]
		if word == '': continue
		text += ' '+word
	if text == '': return ''
	return text[1:]

def SetFromFile(filename,IFLOWER=True):
	ret = set()
	fr = open(filename,'rb')
	for line in fr:
		word = line.strip('\r\n')
		if IFLOWER: word = word.lower()
		if word == '': continue
		ret.add(word)
	fr.close()
	return ret

def EntityIndex(filenames):
	index,n_index = [{}],1
	for filename in filenames:
		fr = open(filename,'rb')
		for line in fr:
			arr = line.strip('\r\n').split('\t')
			if not len(arr) == 2: continue
			entity,classname = arr[0],arr[1]
			words = entity.split(' ')
			n = len(words)
			if n > n_index:
				for i in range(n_index,n):
					index.append({})
				n_index = n
			temp = index[n-1]
			if n > 1:
				for i in range(0,n-1):
					word = words[i]
					if not word in temp: temp[word] = {}
					temp = temp[word]
				word = words[n-1]
			else:
				word = words[0]
			temp[word] = classname
		fr.close()
	return index

def PatternIndex(filename):
	index,n_index = [{}],1
	fr = open(filename,'rb')
	for line in fr:
		arr = line.strip('\r\n').split('\t')
		if len(arr) < 2: continue
		pattern,score = arr[0],float(arr[1])
		sentence = XMLToSentence(pattern)
		keys = SentenceToKeys(sentence)
		n = len(keys)
		if n > n_index:
			for i in range(n_index,n):
				index.append({})
			n_index = n
		temp = index[n-1]
		if n > 1:
			for i in range(0,n-1):
				key = keys[i]
				if not key in temp: temp[key] = {}
				temp = temp[key]
			key = keys[n-1]
		else:
			key = keys[0]
		temp[key] = [pattern,score]		
	fr.close()
	return index

def XMLToSentence(xml):
	periodset = set(['.','?','!'])
	sentence = []
	while '<' in xml:
		pos0 = xml.find('<')
		pos1 = xml.find('>')
		if pos0 > 0:
			part = xml[0:pos0-1]
			if not xml[pos0-1] == ' ':
				part += xml[pos0-1]
			for word in part.split(' '):
				if word in periodset and len(sentence) > 0:
					sentence.append(['PERIOD',word])
					continue
				sentence.append(['',word])
		classname = xml[pos0+1:pos1]
		xml = xml[pos1+1:]
		pos0 = xml.find('<')
		pos1 = xml.find('>')
		if pos0 >= 0:
			words = xml[0:pos0].split(' ')
			sentence.append([classname,words])
		if pos1+1 < len(xml) and xml[pos1+1] == ' ':
			xml = xml[pos1+2:]
		else:
			xml = xml[pos1+1:]
	if len(xml) > 0:
		part = xml[1:]
		if not xml[0] == ' ':
			part = xml[0]+part
		for word in part.split(' '):
			if word in periodset and len(sentence) > 0:
				sentence.append(['PERIOD',word])
				continue
			sentence.append(['',word])
	return sentence

def XMLToSentences(xml):
	periodset = set(['.','?','!'])
	sentences = []
	sentence = []
	while '<' in xml:
		pos0 = xml.find('<')
		pos1 = xml.find('>')
		if pos0 > 0:
			part = xml[0:pos0-1]
			if not xml[pos0-1] == ' ':
				part += xml[pos0-1]
			for word in part.split(' '):
				if word in periodset and len(sentence) > 0:
					sentence.append(['PERIOD',word])
					sentences.append([elem for elem in sentence])
					sentence = []
					continue
				sentence.append(['',word])
		classname = xml[pos0+1:pos1]
		xml = xml[pos1+1:]
		pos0 = xml.find('<')
		pos1 = xml.find('>')
		if pos0 >= 0:
			words = xml[0:pos0].split(' ')
			sentence.append([classname,words])
		if pos1+1 < len(xml) and xml[pos1+1] == ' ':
			xml = xml[pos1+2:]
		else:
			xml = xml[pos1+1:]
	if len(xml) > 0:
		part = xml[1:]
		if not xml[0] == ' ':
			part = xml[0]+part
		for word in part.split(' '):
			if word in periodset and len(sentence) > 0:
				sentence.append(['PERIOD',word])
				sentences.append([elem for elem in sentence])
				sentence = []
				continue
			sentence.append(['',word])
	if len(sentence) > 0:
		sentences.append([elem for elem in sentence])
	return sentences

def SentenceToXML(sentence):
	xml = ''
	for [classname,words] in sentence:
		if classname == '' or classname == 'PERIOD':
			xml += ' '+words
		else:
			entity = ''
			for word in words: entity += ' '+word
			entity = entity[1:]
			xml += ' <'+classname+'>'+entity+'</'+classname+'>'
	if xml == '': return ''
	return xml[1:]

def SentencesToXML(sentences):
	xml = ''
	for sentence in sentences:
		xml += ' '+SentenceToXML(sentence)
	if xml == '': return ''
	return xml[1:]

def SentenceToDollar(sentence):
	dollar = ''
	for [classname,words] in sentence:
		if classname == '' or classname == 'PERIOD':
			dollar += ' '+words
		else:
			_classname = classname
			if '.' in classname:
				pos = classname.rfind('.')
				_classname = classname[pos+1:]
			dollar += ' $'+_classname
	if dollar == '': return ''
	return dollar[1:]

def SentenceToKeys(sentence):
	keys = []
	for [classname,words] in sentence:
		if classname == '' or classname == 'PERIOD':
			keys.append('\t'+words)
		else: 
			keys.append(classname+'\t')
	return keys

