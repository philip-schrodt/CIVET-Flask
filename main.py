## CIVET main.py 
##
## 'main.py' program for the Google App Engine version of the CIVET system 
##
##	PROVENANCE:
##	Programmer: Philip A. Schrodt
##				Parus Analytics
##				Charlottesville, VA, 22901 U.S.A.
##				http://eventdata.parusanalytics.com
##
##	Copyright (c) 2015	Philip A. Schrodt.	All rights reserved.
##
##  The development of CIVET is funded by the U.S. National Science Foundation Office of Multidisciplinary Activities in the 
##  Directorate for Social, Behavioral & Economic Sciences, Award 1338470 and the Odum Institute</a> at the University of 
##  North Carolina at Chapel Hill with additional assistance from Parus Analytics.
##
##  This code is covered under the MIT license: http://opensource.org/licenses/MIT
##
##	Report bugs to: schrodt735@gmail.com
##
##	REVISION HISTORY:
##	12-March-15:	Initial version
##
##	----------------------------------------------------------------------------------
 

from __future__ import print_function
from flask import render_template
from flask import Flask
from flask import request, redirect, url_for
from flask import Response
from flask import send_from_directory

import CIV_template

targetlet = ['a','c','d','e','s','A','C','D','E','S']
tempdata =''

def markup_file(filename):
    newtext = ""
    fin = open("source_texts/"+filename,'r')
    line = fin.readline() 
    while line.find('Text:') != 0:  # could get doc, headline, source info here
        line = fin.readline() 
    line = fin.readline() 
    ka = 0
    while len(line) > 0:  # add the markup
        for let in targetlet:
            tarlet = ' '+let
            letclass = '<span=~="mk' + let.lower() + '">'
            while True:
                if tarlet in line:
                    inda = line.find(tarlet)
                    indb = line.find(' ',inda+1)
                    line = line[:inda+1] + letclass + line[inda+1:indb] + "</span>" + line[indb:]  # use telltail to avoid matching ' c'
#                    print(line)                                        
                    ka += 1
#                    if ka > 14: break
                else: break
        line = line.replace('n=~="','n class="')
        newtext += line
        line = fin.readline() 
        
#    print("Marked text:\n",newtext)
    return newtext

def save_to_tempdata():
    global tempdata
#    print('STT1',CIV_template.savelist)
    for avar in CIV_template.savelist: 
#        print('STT2:',avar)
        if avar in CIV_template.specialvarlist: 
            tempdata += CIV_template.specialvar(avar) + '\t'
        elif avar in CIV_template.constvardict.keys(): 
            tempdata += CIV_template.constvardict[avar] + '\t'
        elif avar in request.form:
            tempdata += request.form[avar]+'\t'
        else:
            tempdata += CIV_template.unchecked[avar] + '\t'
    tempdata = tempdata[:-1] + '\n'
    print('STT3:\n',tempdata)

def create_header():
    global tempdata
    tempdata = ''
    for avar in CIV_template.savelist:  # write the header
        tempdata += avar+'\t'
    tempdata = tempdata[:-1] + '\n'

app = Flask(__name__)
app.config['DEBUG'] = True
basic_mode = True   # normally this will get reset later
create_header()  # this also gets overwritten in normal operation


@app.route('/')
def homepage():
#    CIV_template.imalive()  # debug
    return render_template('index.html')

@app.route('/operating')
def operate():
    return render_template('operating.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/file_select')
def file_select():
    """ case file selection for the text-extraction demo """
    CIV_template.savelist = ['Aword','Cword','Dword','Eword','Sword']
    create_header()
    return render_template('file_select.html')

@app.route('/continue_coding')
def continue_coding():
    if basic_mode:
        return render_template('basic_form.html', form_content = thetemplate)
    else:
        return render_template('file_select.html')

@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, CIVET can find nothing at this URL.', 404

@app.route('/goto_edit', methods=['POST'])
def goto_edit():
    global curfile
    if request.form['inputfile'] != "":
        curfile = request.form['inputfile']
    else:
        curfile = request.form['choosefile']
    return redirect("/extract/"+curfile)

@app.route('/extract/<name>', methods=['POST', 'GET'])
def extractform(name=None):
    global basic_mode
    marked = markup_file(name)
    basic_mode = False
    return render_template('extractor.flask.html', markedtext=marked)
    
@app.route('/save_entry', methods=['POST'])
def save_entry():
    """ save data then return to text extraction form """
    global curfile
    save_to_tempdata()
    return redirect("/extract/"+curfile)

@app.route('/save_basic', methods=['POST'])
def save_basic():
    """ save data then return to template-based form """
    global thetemplate
    save_to_tempdata()
    return render_template('basic_form.html', form_content = thetemplate)

@app.route('/get_new_case', methods=['POST'])
def get_new_case():
    save_to_tempdata()
    return render_template('file_select.html')

@app.route('/display_data', methods=['POST'])
def display_data():
    save_to_tempdata()
    return render_template('download_data.html',filename=CIV_template.defaultfilename)

@app.route('/download_data', methods=['POST'])
def download_data():
    curfilename = request.form['filename']
    if curfilename[-4:] != ".csv":
        curfilename += '.csv'
    return Response(tempdata, 
            mimetype='application/json',
            headers={'Content-Disposition':'attachment;filename=%s' % curfilename}) 

@app.route('/reset_data')
def reset_data():
    create_header()
    if basic_mode:
        return render_template('basic_form.html', form_content = thetemplate)
    else:
        return render_template('file_select.html')

@app.route('/select_template')
def select_template():
    return render_template('template_select.html')

@app.route('/use_demotemplate',methods=['POST'])
def use_demotemplate():
    fin = open('static/CIVET.demo.template.txt','r')
    for ka in range(8):
        line = fin.readline()
        print(line)
    fin.close()
    return render_template('template_select.html')

@app.route('/read_template',methods=['POST'])
def read_template():
    """ main routine for setting up a template: reads a file, checks for errors, and then either renders the form or 
        lists the errors """
    global thetemplate, basic_mode
    CIV_template.init_template()
    if 'codername' in request.form:
#        print('RTcn: codername',request.form['codername'] )
        CIV_template.codername = request.form['codername']        
    """print('RT keys',request.form.keys() )
    print('RT file keys',request.files.keys() )
    print('RT2*:',request.files['template_name'].filename) """       
    if len(request.files['template_name'].filename) > 0:
#        print('RT2:',request.files['template_name'].filename)        
        st = request.files.get('template_name')
    else:
#        print('RT: Use demo')
        st = open('static/CIVET.demo.template.txt','r')
    thecontent = ''
    commln = CIV_template.get_commlines(st)
    while len(commln) > 0:
        thecontent += CIV_template.do_command(commln)
        commln = CIV_template.get_commlines(st)

#    print('thecontent:',thecontent)
    if len(CIV_template.savelist) == 0:
        thecontent += '~Error~<p>A "save:" command is required in the template<br>\n'
    else:
        misslist = []
        for ele in CIV_template.savelist:
            if ele not in CIV_template.varlist:
                misslist.append(ele)
        if len(misslist) > 0:
            thecontent += '~Error~<p>The following variables are in the "save:" command but were not declared in a data field<br>' + str(misslist) + '\n'

    if '~Error~' in thecontent:
        errortext = ''
        indx = thecontent.find('~Error~')
        while indx >= 0:
            indy = thecontent.find('\n',indx)
            errortext += thecontent[indx+7:indy+1]
            indx = thecontent.find('~Error~',indy)
        return render_template('template_error.html', form_content = errortext)
    else:
        thetemplate = thecontent
        create_header()
        basic_mode = True
        return render_template('basic_form.html', form_content = thecontent)

@app.route('/download_pdfdocs')
def download_pdfdocs():
    return send_from_directory('static','CIVET.Documentation.pdf', as_attachment=True)

@app.route('/download_demotemplate')
def download_demotemplate():
    return send_from_directory('static','CIVET.demo.template.txt', as_attachment=True)
