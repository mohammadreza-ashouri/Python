__all__ = ['commonTools']

# Don't look below, you will not understand this Python code :) I don't.

from js2py.pyjs import *
# setting scope
var = Scope( JS_BUILTINS )
set_global_object(var)

# Code follows:
var.registers(['ontology2FullObjects', 'camelCase', 'hierarchy2String', 'uuidv4', 'editString2Docs', 'ontology2Labels', 'getChildren', 'fillDocBeforeCreate', 'doc2SortedDoc'])
@Js
def PyJsHoisted_uuidv4_(this, arguments, var=var):
    var = Scope({'this':this, 'arguments':arguments}, var)
    var.registers([])
    @Js
    def PyJs_anonymous_0_(c, this, arguments, var=var):
        var = Scope({'c':c, 'this':this, 'arguments':arguments}, var)
        var.registers(['v', 'c', 'r'])
        var.put('r', ((var.get('Math').callprop('random')*Js(16.0))|Js(0.0)))
        var.put('v', (var.get('r') if PyJsStrictEq(var.get('c'),Js('x')) else (var.get('r')&(Js(3)|Js(8)))))
        return var.get('v').callprop('toString', Js(16.0))
    PyJs_anonymous_0_._set_name('anonymous')
    return Js('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx').callprop('replace', JsRegExp('/[x]/g'), PyJs_anonymous_0_)
PyJsHoisted_uuidv4_.func_name = 'uuidv4'
var.put('uuidv4', PyJsHoisted_uuidv4_)
@Js
def PyJsHoisted_fillDocBeforeCreate_(data, docType, prefix, this, arguments, var=var):
    var = Scope({'data':data, 'docType':docType, 'prefix':prefix, 'this':this, 'arguments':arguments}, var)
    var.registers(['now', 'rating', 'line', 'data', 'prefix', 'keys', 'prefixJ', 'otherTags', 'text', 'i', 'docType', 'initSpaces', 'fields'])
    var.put('keys', var.get('Object').callprop('keys', var.get('data')))
    if var.get('data').get('type').neg():
        if PyJsStrictEq(var.get('docType'),Js('project')):
            var.get('data').put('type', Js([Js('text'), var.get('docType')]))
        else:
            var.get('data').put('type', Js([var.get('docType')]))
    if (PyJsStrictEq(var.get('data').get('type').typeof(),Js('string')) or var.get('data').get('type').instanceof(var.get('String'))):
        var.get('data').put('type', var.get('data').get('type').callprop('split', Js('/')))
    if var.get('prefix').neg():
        var.put('prefix', var.get('docType').get('0').get('0'))
    if var.get('data').get('_id').neg():
        var.get('data').put('_id', ((var.get('prefix')+Js('-'))+var.get('uuidv4')()))
    var.get('data').put('nextRevision', Js(0.0))
    var.put('now', var.get('Date').create())
    var.get('data').put('date', var.get('now').callprop('toISOString'))
    if var.get('data').get('branch').neg():
        var.get('data').put('branch', Js([Js({'stack':Js([var.get(u"null")])})]))
    if var.get('data').get('comment').neg():
        var.get('data').put('comment', Js(''))
    if var.get('data').get('tags').neg():
        var.put('rating', var.get('data').get('comment').callprop('match', JsRegExp('/#\\d/')))
        if PyJsStrictEq(var.get('rating'),var.get(u"null")):
            var.put('rating', Js([]))
        var.put('otherTags', var.get('data').get('comment').callprop('match', JsRegExp('/#\\D[\\S]+/g')))
        if PyJsStrictEq(var.get('otherTags'),var.get(u"null")):
            var.put('otherTags', Js([]))
        var.get('data').put('tags', var.get('rating').callprop('concat', var.get('otherTags')))
        var.get('data').put('comment', var.get('data').get('comment').callprop('replace', JsRegExp('/#[\\S]+/g'), Js('')))
        var.put('fields', var.get('data').get('comment').callprop('match', JsRegExp('/:[\\S]+:[\\S]+:/g')))
        if (var.get('fields')!=var.get(u"null")):
            @Js
            def PyJs_anonymous_1_(item, this, arguments, var=var):
                var = Scope({'item':item, 'this':this, 'arguments':arguments}, var)
                var.registers(['item', 'aList'])
                var.put('aList', var.get('item').callprop('split', Js(':')))
                if var.get('isNaN')(var.get('aList').get('2')):
                    return var.get('data').put(var.get('aList').get('1'), var.get('aList').get('2'))
                else:
                    return var.get('data').put(var.get('aList').get('1'), (+var.get('aList').get('2')))
            PyJs_anonymous_1_._set_name('anonymous')
            var.get('fields').callprop('map', PyJs_anonymous_1_)
        var.get('data').put('comment', var.get('data').get('comment').callprop('replace', JsRegExp('/:[\\S]+:[\\S]+:/g'), Js('')))
        var.put('text', var.get('data').get('comment').callprop('split', Js('\n')))
        var.get('data').put('comment', Js(''))
        #for JS loop
        var.put('i', Js(0.0))
        while (var.get('i')<var.get('text').get('length')):
            try:
                var.put('line', var.get('text').get(var.get('i')))
                var.put('initSpaces', var.get('line').callprop('search', JsRegExp('/\\S|$/')))
                #for JS loop
                var.put('prefixJ', Js(''))
                while (var.get('prefixJ').get('length')<(var.get('Math').callprop('round', (var.get('initSpaces')/Js(2.0)))*Js(2.0))):
                    try:
                        pass
                    finally:
                            var.put('prefixJ', Js(' '), '+')
                var.get('data').put('comment', ((var.get('prefixJ')+var.get('line').callprop('trim'))+Js('\n')), '+')
            finally:
                    (var.put('i',Js(var.get('i').to_number())+Js(1))-Js(1))
        var.get('data').put('comment', var.get('data').get('comment').callprop('substring', Js(0.0), (var.get('data').get('comment').get('length')-Js(1.0))))
    if (PyJsStrictEq(var.get('data').get('tags').typeof(),Js('string')) or var.get('data').get('tags').instanceof(var.get('String'))):
        var.get('data').put('tags', var.get('data').get('tags').callprop('split', Js(' ')))
    if var.get('data').get('path'):
        var.get('console').callprop('log', Js('cT got path'))
        var.get('console').callprop('log', var.get('data'))
        var.get('data').delete('path')
    if PyJsStrictEq(var.get('data').get('type').get('0'),Js('sample')):
        if var.get('data').get('qrCode').neg():
            var.get('data').put('qrCode', Js([]))
        if (PyJsStrictEq(var.get('data').get('qrCode').typeof(),Js('string')) or var.get('data').get('qrCode').instanceof(var.get('String'))):
            var.get('data').put('qrCode', var.get('data').get('qrCode').callprop('split', Js(' ')))
    if PyJsStrictEq(var.get('data').get('type').get('0'),Js('measurement')):
        if var.get('data').get('image').neg():
            var.get('data').put('image', Js(''))
        if var.get('data').get('shasum').neg():
            var.get('data').put('shasum', Js(''))
    @Js
    def PyJs_anonymous_2_(key, this, arguments, var=var):
        var = Scope({'key':key, 'this':this, 'arguments':arguments}, var)
        var.registers(['key'])
        if (PyJsStrictEq(var.get('data').get(var.get('key')).typeof(),Js('string')) or var.get('data').get(var.get('key')).instanceof(var.get('String'))):
            var.get('data').put(var.get('key'), var.get('data').get(var.get('key')).callprop('trim'))
        return var.get('data').get(var.get('key'))
    PyJs_anonymous_2_._set_name('anonymous')
    var.get('keys').callprop('map', PyJs_anonymous_2_)
    return var.get('data')
PyJsHoisted_fillDocBeforeCreate_.func_name = 'fillDocBeforeCreate'
var.put('fillDocBeforeCreate', PyJsHoisted_fillDocBeforeCreate_)
@Js
def PyJsHoisted_ontology2Labels_(ontology, tableFormat, this, arguments, var=var):
    var = Scope({'ontology':ontology, 'tableFormat':tableFormat, 'this':this, 'arguments':arguments}, var)
    var.registers(['ontology', 'dataList', 'tableFormat', 'hierarchyList', 'outList'])
    @Js
    def PyJs_anonymous_3_(key, this, arguments, var=var):
        var = Scope({'key':key, 'this':this, 'arguments':arguments}, var)
        var.registers(['label', 'key'])
        if ((PyJsStrictEq(var.get('key').get('0'),Js('-')) or PyJsStrictEq(var.get('key').get('0'),Js('_'))) or (var.get('ontology').get('-hierarchy-').callprop('indexOf', var.get('key'))>=Js(1.0))):
            return Js([var.get(u"null"), var.get(u"null")])
        else:
            var.put('label', ((var.get('key').get('0').callprop('toUpperCase')+var.get('key').callprop('slice', Js(1.0)))+Js('s')))
        if (var.get('tableFormat').get(var.get('key')) and var.get('tableFormat').get(var.get('key')).get('-label-')):
            var.put('label', var.get('tableFormat').get(var.get('key')).get('-label-'))
        return Js([var.get('key'), var.get('label')])
    PyJs_anonymous_3_._set_name('anonymous')
    var.put('outList', var.get('Object').callprop('keys', var.get('ontology')).callprop('map', PyJs_anonymous_3_))
    @Js
    def PyJs_anonymous_4_(value, this, arguments, var=var):
        var = Scope({'value':value, 'this':this, 'arguments':arguments}, var)
        var.registers(['value'])
        return (var.get('value').get('0')!=var.get(u"null"))
    PyJs_anonymous_4_._set_name('anonymous')
    var.put('outList', var.get('outList').callprop('filter', PyJs_anonymous_4_))
    @Js
    def PyJs_anonymous_5_(value, this, arguments, var=var):
        var = Scope({'value':value, 'this':this, 'arguments':arguments}, var)
        var.registers(['value'])
        return (var.get('ontology').get('-hierarchy-').callprop('indexOf', var.get('value').get('0'))<Js(0.0))
    PyJs_anonymous_5_._set_name('anonymous')
    var.put('dataList', var.get('outList').callprop('filter', PyJs_anonymous_5_))
    @Js
    def PyJs_anonymous_6_(value, this, arguments, var=var):
        var = Scope({'value':value, 'this':this, 'arguments':arguments}, var)
        var.registers(['value'])
        return (var.get('ontology').get('-hierarchy-').callprop('indexOf', var.get('value').get('0'))>=Js(0.0))
    PyJs_anonymous_6_._set_name('anonymous')
    var.put('hierarchyList', var.get('outList').callprop('filter', PyJs_anonymous_6_))
    return Js({'dataList':var.get('dataList'),'hierarchyList':var.get('hierarchyList')})
PyJsHoisted_ontology2Labels_.func_name = 'ontology2Labels'
var.put('ontology2Labels', PyJsHoisted_ontology2Labels_)
@Js
def PyJsHoisted_ontology2FullObjects_(scheme, colWidth, this, arguments, var=var):
    var = Scope({'scheme':scheme, 'colWidth':colWidth, 'this':this, 'arguments':arguments}, var)
    var.registers(['colWidth', 'scheme', 'addZeros'])
    if var.get('colWidth'):
        var.put('colWidth', var.get('colWidth').get('-default-'))
    else:
        var.put('colWidth', Js([Js(25.0), Js(25.0), Js(25.0), Js(25.0)]))
    var.put('addZeros', (var.get('scheme').get('length')-var.get('colWidth').get('length')))
    var.put('colWidth', var.get('colWidth').callprop('concat', var.get('Array')(var.get('addZeros')).callprop('fill', Js(0.0))))
    @Js
    def PyJs_anonymous_7_(item, idx, this, arguments, var=var):
        var = Scope({'item':item, 'idx':idx, 'this':this, 'arguments':arguments}, var)
        var.registers(['idx', 'item'])
        var.get('item').put('colWidth', var.get('colWidth').get(var.get('idx')))
        if var.get('item').get('unit').neg():
            var.get('item').put('unit', Js(''))
        if var.get('item').get('required').neg():
            var.get('item').put('required', Js(False))
        if var.get('item').get('list').neg():
            var.get('item').put('list', var.get(u"null"))
        return var.get('item')
    PyJs_anonymous_7_._set_name('anonymous')
    var.put('scheme', var.get('scheme').callprop('map', PyJs_anonymous_7_))
    return var.get('scheme')
PyJsHoisted_ontology2FullObjects_.func_name = 'ontology2FullObjects'
var.put('ontology2FullObjects', PyJsHoisted_ontology2FullObjects_)
@Js
def PyJsHoisted_hierarchy2String_(data, addID, callback, detail, magicTags, this, arguments, var=var):
    var = Scope({'data':data, 'addID':addID, 'callback':callback, 'detail':detail, 'magicTags':magicTags, 'this':this, 'arguments':arguments}, var)
    var.registers(['compare', 'dataList', 'addID', 'callback', 'key', 'data', 'outString', 'id', 'hierarchyIDs', 'keys', 'magicTags', 'detail', 'value', 'childNum', 'i', 'j', 'hierString'])
    @Js
    def PyJsHoisted_compare_(a, b, this, arguments, var=var):
        var = Scope({'a':a, 'b':b, 'this':this, 'arguments':arguments}, var)
        var.registers(['b', 'a'])
        if (var.get('a').get('hierarchy')>var.get('b').get('hierarchy')):
            return Js(1.0)
        else:
            return (-Js(1.0))
    PyJsHoisted_compare_.func_name = 'compare'
    var.put('compare', PyJsHoisted_compare_)
    var.put('dataList', Js([]))
    var.put('keys', var.get('Object').callprop('keys', var.get('data')))
    var.put('hierString', var.get(u"null"))
    #for JS loop
    var.put('i', Js(0.0))
    while (var.get('i')<var.get('keys').get('length')):
        try:
            var.put('key', var.get('keys').get(var.get('i')))
            var.put('value', var.get('data').get(var.get('key')))
            if PyJsStrictEq(var.get('value').get('0'),var.get('key')):
                var.put('hierString', var.get('key'))
            else:
                var.put('hierarchyIDs', var.get('value').get('0').callprop('split', Js(' ')))
                var.put('hierString', var.get('hierarchyIDs').get('0'))
                #for JS loop
                var.put('j', Js(1.0))
                while (var.get('j')<var.get('hierarchyIDs').get('length')):
                    try:
                        var.put('id', var.get('hierarchyIDs').get(var.get('j')))
                        var.put('childNum', Js(0.0))
                        if var.get('data').contains(var.get('id')):
                            var.put('childNum', var.get('data').get(var.get('id')).get('1'))
                        if (var.get('childNum')>Js(9999.0)):
                            var.get('console').callprop('log', (Js('**ERROR** commonTools:ChildNUM>9999 **ERROR** ')+var.get('key')))
                        var.put('hierString', (((Js(' ')+(Js('00')+var.get('childNum')).callprop('substr', (-Js(3.0))))+Js(' '))+var.get('id')), '+')
                    finally:
                            (var.put('j',Js(var.get('j').to_number())+Js(1))-Js(1))
            var.get('dataList').callprop('push', Js({'hierarchy':var.get('hierString'),'label':var.get('value').callprop('slice', Js(2.0))}))
        finally:
                (var.put('i',Js(var.get('i').to_number())+Js(1))-Js(1))
    pass
    var.get('dataList').callprop('sort', var.get('compare'))
    @Js
    def PyJs_anonymous_8_(item, this, arguments, var=var):
        var = Scope({'item':item, 'this':this, 'arguments':arguments}, var)
        var.registers(['i', 'i2', 'i1', 'partString', 'prefix', 'item', 'docID', 'i3', 'spaces', 'hierarchyArray', 'doc'])
        var.put('hierarchyArray', var.get('item').get('hierarchy').callprop('split', Js(' ')))
        var.put('spaces', ((var.get('hierarchyArray').get('length')/Js(2.0))-Js(0.5)))
        #for JS loop
        var.put('prefix', Js(''))
        while (var.get('prefix').get('length')<=var.get('spaces')):
            try:
                pass
            finally:
                    var.put('prefix', Js('*'), '+')
        if PyJsStrictEq(var.get('addID'),Js(True)):
            var.put('partString', var.get('item').get('label').get('1'))
            var.put('docID', var.get('hierarchyArray').get((var.get('hierarchyArray').get('length')-Js(1.0))))
            var.put('partString', (Js('||')+var.get('docID')), '+')
            if PyJsStrictEq(var.get('callback',throw=False).typeof(),Js('function')):
                var.put('doc', var.get('callback')(var.get('docID')))
                if PyJsStrictEq(var.get('detail'),Js('all')):
                    #for JS loop
                    var.put('i', Js(0.0))
                    while (var.get('i')<var.get('doc').get('branch').get('length')):
                        try:
                            var.put('partString', (Js('\nPath: ')+var.get('doc').get('branch').get(var.get('i')).get('path')), '+')
                        finally:
                                (var.put('i',Js(var.get('i').to_number())+Js(1))-Js(1))
                    var.put('partString', Js('\nInheritance: '), '+')
                    #for JS loop
                    var.put('i1', Js(0.0))
                    while (var.get('i1')<var.get('doc').get('branch').get('length')):
                        try:
                            var.put('partString', (var.get('doc').get('branch').get(var.get('i1')).get('stack')+Js(' ')), '+')
                        finally:
                                (var.put('i1',Js(var.get('i1').to_number())+Js(1))-Js(1))
                if PyJsStrictEq(var.get('doc').get('type'),Js('project')):
                    var.put('partString', (Js('\nObjective: ')+var.get('doc').get('objective')), '+')
                #for JS loop
                var.put('i2', Js(0.0))
                while (var.get('i2')<var.get('magicTags').get('length')):
                    try:
                        if (var.get('doc').get('tags').callprop('indexOf', (Js('#')+var.get('magicTags').get(var.get('i2'))))>(-Js(1.0))):
                            var.put('prefix', ((var.get('prefix')+Js(' '))+var.get('magicTags').get(var.get('i2'))))
                            #for JS loop
                            var.put('i3', Js(0.0))
                            while (var.get('i3')<var.get('doc').get('tags').get('length')):
                                try:
                                    if PyJsStrictEq(var.get('doc').get('tags').get(var.get('i3')),(Js('#')+var.get('magicTags').get(var.get('i2')))):
                                        var.get('doc').get('tags').callprop('splice', var.get('i'), Js(1.0))
                                        (var.put('i',Js(var.get('i').to_number())-Js(1))+Js(1))
                                finally:
                                        (var.put('i3',Js(var.get('i3').to_number())+Js(1))-Js(1))
                    finally:
                            (var.put('i2',Js(var.get('i2').to_number())+Js(1))-Js(1))
                var.put('partString', (((Js('\nTags: ')+var.get('doc').get('tags').callprop('join', Js(' ')))+Js('\n'))+var.get('doc').get('comment')), '+')
            var.put('partString', ((var.get('prefix')+Js(' '))+var.get('partString')))
        else:
            var.put('partString', ((((var.get('prefix')+Js(' '))+var.get('item').get('label').get('0'))+Js(': '))+var.get('item').get('label').get('1')))
        return var.get('partString')
    PyJs_anonymous_8_._set_name('anonymous')
    var.put('outString', var.get('dataList').callprop('map', PyJs_anonymous_8_))
    return var.get('outString').callprop('join', Js('\n'))
PyJsHoisted_hierarchy2String_.func_name = 'hierarchy2String'
var.put('hierarchy2String', PyJsHoisted_hierarchy2String_)
@Js
def PyJsHoisted_editString2Docs_(text, magicTags, this, arguments, var=var):
    var = Scope({'text':text, 'magicTags':magicTags, 'this':this, 'arguments':arguments}, var)
    var.registers(['i', 'objective', 'j', 'line', 'docs', 'comment', 'tags', 'magicTags', 'text', 'docID', 'parts', 'docType', 'title'])
    var.put('docs', Js([]))
    var.put('objective', Js(''))
    var.put('tags', Js(''))
    var.put('comment', Js(''))
    var.put('title', Js(''))
    var.put('docID', Js(''))
    var.put('docType', Js(''))
    var.put('text', var.get('text').callprop('split', Js('\n')))
    #for JS loop
    var.put('i', Js(0.0))
    while (var.get('i')<var.get('text').get('length')):
        try:
            var.put('line', var.get('text').get(var.get('i')))
            if ((PyJsStrictEq(var.get('line').callprop('substring', Js(0.0), Js(2.0)),Js('* ')) or PyJsStrictEq(var.get('line').callprop('substring', Js(0.0), Js(3.0)),Js('** '))) or PyJsStrictEq(var.get('line').callprop('substring', Js(0.0), Js(4.0)),Js('*** '))):
                var.put('comment', var.get('comment').callprop('trim'))
                if PyJsStrictNeq(var.get('title'),Js('')):
                    if PyJsStrictEq(var.get('docID'),Js('')):
                        var.get('docs').callprop('push', Js({'edit':Js('-new-'),'name':var.get('title'),'objective':var.get('objective'),'tags':var.get('tags'),'comment':var.get('comment'),'_id':var.get('docID'),'type':var.get('docType')}))
                    else:
                        var.get('docs').callprop('push', Js({'edit':Js('-edit-'),'name':var.get('title'),'objective':var.get('objective'),'tags':var.get('tags'),'comment':var.get('comment'),'_id':var.get('docID'),'type':var.get('docType')}))
                else:
                    if (var.get('docID')!=Js('')):
                        var.get('docs').callprop('push', Js({'edit':Js('-delete-'),'name':var.get('title'),'objective':var.get('objective'),'tags':var.get('tags'),'comment':var.get('comment'),'_id':var.get('docID'),'type':var.get('docType')}))
                var.put('objective', Js(''))
                var.put('tags', Js(''))
                var.put('comment', Js(''))
                var.put('title', Js(''))
                var.put('docID', Js(''))
                var.put('docType', Js(''))
                var.put('parts', var.get('line').callprop('split', Js('||')))
                var.put('title', var.get('parts').get('0').callprop('split', Js(' ')).callprop('slice', Js(1.0)).callprop('join', Js(' ')))
                #for JS loop
                var.put('j', (var.get('magicTags').get('length')-Js(1.0)))
                while (var.get('j')>=Js(0.0)):
                    try:
                        if PyJsStrictEq(var.get('title').callprop('substring', Js(0.0), Js(4.0)),var.get('magicTags').get(var.get('j'))):
                            var.put('title', var.get('title').callprop('slice', (var.get('magicTags').get(var.get('j')).get('length')+Js(1.0))))
                            var.put('tags', ((Js('#')+var.get('magicTags').get(var.get('j')))+Js(' ')), '+')
                    finally:
                            (var.put('j',Js(var.get('j').to_number())-Js(1))+Js(1))
                var.put('tags', var.get('tags').callprop('trim'))
                if (var.get('parts').get('length')>Js(1.0)):
                    var.put('docID', var.get('parts').get((var.get('parts').get('length')-Js(1.0))))
                var.put('docType', (var.get('line').callprop('split', Js(' ')).get('0').get('length')-Js(1.0)))
            else:
                if PyJsStrictEq(var.get('line').callprop('substring', Js(0.0), Js(10.0)),Js('Objective:')):
                    var.put('objective', var.get('line').callprop('substring', Js(10.0), var.get('line').get('length')).callprop('trim'))
                else:
                    if PyJsStrictEq(var.get('line').callprop('substring', Js(0.0), Js(5.0)),Js('Tags:')):
                        var.put('tags', var.get('line').callprop('substring', Js(5.0), var.get('line').get('length')).callprop('trim'), '+')
                    else:
                        var.put('comment', (var.get('line')+Js('\n')), '+')
        finally:
                (var.put('i',Js(var.get('i').to_number())+Js(1))-Js(1))
    var.put('comment', var.get('comment').callprop('trim'))
    if PyJsStrictNeq(var.get('title'),Js('')):
        if PyJsStrictEq(var.get('docID'),Js('')):
            var.get('docs').callprop('push', Js({'edit':Js('-new-'),'name':var.get('title'),'objective':var.get('objective'),'tags':var.get('tags'),'comment':var.get('comment'),'_id':var.get('docID'),'type':var.get('docType')}))
        else:
            var.get('docs').callprop('push', Js({'edit':Js('-edit-'),'name':var.get('title'),'objective':var.get('objective'),'tags':var.get('tags'),'comment':var.get('comment'),'_id':var.get('docID'),'type':var.get('docType')}))
    else:
        if (var.get('docID')!=Js('')):
            var.get('docs').callprop('push', Js({'edit':Js('-delete-'),'name':var.get('title'),'objective':var.get('objective'),'tags':var.get('tags'),'comment':var.get('comment'),'_id':var.get('docID'),'type':var.get('docType')}))
    return var.get('docs')
PyJsHoisted_editString2Docs_.func_name = 'editString2Docs'
var.put('editString2Docs', PyJsHoisted_editString2Docs_)
@Js
def PyJsHoisted_getChildren_(data, docID, this, arguments, var=var):
    var = Scope({'data':data, 'docID':docID, 'this':this, 'arguments':arguments}, var)
    var.registers(['names', 'numStarsParent', 'data', 'lines', 'nStars', 'ids', 'saveLine', 'docID', 'i', 'items'])
    var.put('names', Js([]))
    var.put('ids', Js([]))
    var.put('saveLine', Js(False))
    var.put('numStarsParent', (-Js(1.0)))
    var.put('lines', var.get('data').callprop('split', Js('\n')))
    #for JS loop
    var.put('i', Js(0.0))
    while (var.get('i')<var.get('lines').get('length')):
        try:
            var.put('items', var.get('lines').get(var.get('i')).callprop('split', Js('||')))
            if var.get('saveLine'):
                var.put('nStars', var.get('items').get('0').callprop('split', Js(' ')).get('0').get('length'))
                if PyJsStrictEq(var.get('nStars'),var.get('numStarsParent')):
                    break
                if PyJsStrictEq(var.get('nStars'),(var.get('numStarsParent')+Js(1.0))):
                    var.get('ids').callprop('push', var.get('items').get('1'))
                    var.get('names').callprop('push', var.get('items').get('0').callprop('substring', (var.get('numStarsParent')+Js(2.0))))
            if PyJsStrictEq(var.get('items').get('1'),var.get('docID')):
                if PyJsStrictEq(var.get('items').get('0').get('0'),Js('*')):
                    var.put('numStarsParent', var.get('items').get('0').callprop('split', Js(' ')).get('length'))
                else:
                    var.put('numStarsParent', Js(0.0))
                var.put('saveLine', Js(True))
        finally:
                (var.put('i',Js(var.get('i').to_number())+Js(1))-Js(1))
    return Js({'names':var.get('names'),'ids':var.get('ids')})
PyJsHoisted_getChildren_.func_name = 'getChildren'
var.put('getChildren', PyJsHoisted_getChildren_)
@Js
def PyJsHoisted_doc2SortedDoc_(doc, tableMeta, this, arguments, var=var):
    var = Scope({'doc':doc, 'tableMeta':tableMeta, 'this':this, 'arguments':arguments}, var)
    var.registers(['valuesMain', 'valuesDetail', 'valuesImage', 'metaUser', 'keysDB', 'tableMeta', 'keysDetail', 'valuesDB', 'metaVendor', 'doc', 'keysMain'])
    var.put('valuesImage', var.get('doc').get('image'))
    var.get('doc').delete('image')
    @Js
    def PyJs_anonymous_9_(item, this, arguments, var=var):
        var = Scope({'item':item, 'this':this, 'arguments':arguments}, var)
        var.registers(['item'])
        return var.get('item').get('name')
    PyJs_anonymous_9_._set_name('anonymous')
    var.put('keysMain', var.get('tableMeta').callprop('map', PyJs_anonymous_9_))
    @Js
    def PyJs_anonymous_10_(key, this, arguments, var=var):
        var = Scope({'key':key, 'this':this, 'arguments':arguments}, var)
        var.registers(['key', 'value'])
        var.put('value', var.get('doc').get(var.get('key')))
        if (PyJsStrictEq(var.get('value',throw=False).typeof(),Js('string')) or var.get('value').instanceof(var.get('String'))).neg():
            if var.get('value').neg():
                var.put('value', Js(''))
            else:
                if PyJsStrictEq(var.get('key'),Js('type')):
                    var.put('value', var.get('value').callprop('join', Js('/')))
                else:
                    var.put('value', var.get('value').callprop('toString'))
        var.get('doc').delete(var.get('key'))
        return var.get('value')
    PyJs_anonymous_10_._set_name('anonymous')
    var.put('valuesMain', var.get('keysMain').callprop('map', PyJs_anonymous_10_))
    var.get('doc').delete('branch')
    var.put('metaVendor', var.get('doc').get('metaVendor'))
    var.put('metaUser', var.get('doc').get('metaUser'))
    var.get('doc').delete('metaVendor')
    var.get('doc').delete('metaUser')
    var.put('keysDB', Js([Js('type'), Js('_id'), Js('_rev'), Js('client'), Js('user')]))
    @Js
    def PyJs_anonymous_11_(key, this, arguments, var=var):
        var = Scope({'key':key, 'this':this, 'arguments':arguments}, var)
        var.registers(['key', 'value'])
        var.put('value', var.get('doc').get(var.get('key')))
        if PyJsStrictEq(var.get('key'),Js('childs')):
            var.put('value', var.get('doc').get(var.get('key')).get('length').callprop('toString'))
        var.get('doc').delete(var.get('key'))
        return var.get('value')
    PyJs_anonymous_11_._set_name('anonymous')
    var.put('valuesDB', var.get('keysDB').callprop('map', PyJs_anonymous_11_))
    var.put('keysDetail', var.get('Object').callprop('keys', var.get('doc')))
    @Js
    def PyJs_anonymous_12_(key, this, arguments, var=var):
        var = Scope({'key':key, 'this':this, 'arguments':arguments}, var)
        var.registers(['key'])
        return var.get('doc').get(var.get('key'))
    PyJs_anonymous_12_._set_name('anonymous')
    var.put('valuesDetail', var.get('keysDetail').callprop('map', PyJs_anonymous_12_))
    return Js({'keysMain':var.get('keysMain'),'valuesMain':var.get('valuesMain'),'keysDetail':var.get('keysDetail'),'valuesDetail':var.get('valuesDetail'),'keysDB':var.get('keysDB'),'valuesDB':var.get('valuesDB'),'image':var.get('valuesImage'),'metaVendor':var.get('metaVendor'),'metaUser':var.get('metaUser')})
PyJsHoisted_doc2SortedDoc_.func_name = 'doc2SortedDoc'
var.put('doc2SortedDoc', PyJsHoisted_doc2SortedDoc_)
@Js
def PyJsHoisted_camelCase_(str, this, arguments, var=var):
    var = Scope({'str':str, 'this':this, 'arguments':arguments}, var)
    var.registers(['str', 'outString'])
    @Js
    def PyJs_anonymous_13_(match, this, arguments, var=var):
        var = Scope({'match':match, 'this':this, 'arguments':arguments}, var)
        var.registers(['match'])
        if JsRegExp('/\\s+/').callprop('test', var.get('match')):
            return Js('')
        return var.get('match').callprop('toUpperCase')
    PyJs_anonymous_13_._set_name('anonymous')
    var.put('outString', var.get('str').callprop('replace', JsRegExp('/(?:^\\w|[A-Z]|\\b\\w|\\s+)/g'), PyJs_anonymous_13_))
    var.put('outString', var.get('outString').callprop('replace', JsRegExp('/\\W/g'), Js('')))
    return var.get('outString')
PyJsHoisted_camelCase_.func_name = 'camelCase'
var.put('camelCase', PyJsHoisted_camelCase_)
pass
pass
pass
pass
pass
pass
pass
pass
pass
pass


# Add lib to the module scope
commonTools = var.to_python()