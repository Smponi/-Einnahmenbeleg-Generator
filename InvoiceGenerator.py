from tkinter import *
import os
import pdfrw 
fields = 'Beleg Nummer', 'Brutto', 'MwSatz', 'Mwst', 'Netto', 'Betrag in Worten', 'Zahlung von', 'Jahr', 'Ort', 'Kontierung','Verwendungszweck'
months = 'Jan','Feb','Mär','Apr','Mai','Jun','Jul','Aug','Sep','Okt','Nov','Dez'
template = pdfrw.PdfReader('Einnahmbeleg.pdf')

def createPDF(entries):
    global dict
    dict = {}
    counter = 1
    for entry in entries:
        field = entry[0]
        text  = entry[1].get()
        dict[field] = text
    createBaseTemplate()
    if(check1.get() == 1):
        for month in months:
            fileName=dict['Zahlung von']+dict['Jahr']+month+".pdf"
            template.Root.Pages.Kids[0].Annots[7].update(pdfrw.PdfDict(V=dict['Verwendungszweck']+" " +month+" "+dict['Jahr']))
            template.Root.Pages.Kids[0].Annots[17].update(pdfrw.PdfDict(V=dict['Verwendungszweck']+" " +month+" "+dict['Jahr']))

            template.Root.Pages.Kids[0].Annots[8].update(pdfrw.PdfDict(V=dict['Ort'] +"/" " 1." +str(counter) +"." + dict['Jahr']))
            template.Root.Pages.Kids[0].Annots[18].update(pdfrw.PdfDict(V=dict['Ort'] +"/" " 1." +str(counter) +"." + dict['Jahr']))
            pdfrw.PdfWriter().write(fileName, template)
            counter=counter+1
    else:
        fileName=dict['Zahlung von']+dict['Jahr']+".pdf"
        template.Root.Pages.Kids[0].Annots[7].update(pdfrw.PdfDict(V=dict['Verwendungszweck']))
        template.Root.Pages.Kids[0].Annots[17].update(pdfrw.PdfDict(V=dict['Verwendungszweck']))
        pdfrw.PdfWriter().write(fileName, template)
    print("Dokumente erfolgreich erstellt.")


def makeform(root, fields):
   entries = []
   for field in fields:
      row = Frame(root)
      lab = Label(row, width=15, text=field, anchor='w')
      ent = Entry(row)
      row.pack(side=TOP, fill=X, padx=5, pady=5)
      lab.pack(side=LEFT)
      ent.pack(side=RIGHT, expand=YES, fill=X)
      entries.append((field, ent))
   return entries

def createBaseTemplate():
    template.Root.Pages.Kids[0].Annots[0].update(pdfrw.PdfDict(V=dict['Beleg Nummer']))
    template.Root.Pages.Kids[0].Annots[10].update(pdfrw.PdfDict(V=dict['Beleg Nummer']))
    
    template.Root.Pages.Kids[0].Annots[1].update(pdfrw.PdfDict(V=dict['Brutto']))
    template.Root.Pages.Kids[0].Annots[11].update(pdfrw.PdfDict(V=dict['Brutto']))
    
    template.Root.Pages.Kids[0].Annots[2].update(pdfrw.PdfDict(V=dict['MwSatz']))
    template.Root.Pages.Kids[0].Annots[12].update(pdfrw.PdfDict(V=dict['MwSatz']))
    
    template.Root.Pages.Kids[0].Annots[3].update(pdfrw.PdfDict(V=dict['Mwst']))
    template.Root.Pages.Kids[0].Annots[13].update(pdfrw.PdfDict(V=dict['Mwst']))
    
    template.Root.Pages.Kids[0].Annots[4].update(pdfrw.PdfDict(V=dict['Netto']))
    template.Root.Pages.Kids[0].Annots[14].update(pdfrw.PdfDict(V=dict['Netto']))
    
    template.Root.Pages.Kids[0].Annots[5].update(pdfrw.PdfDict(V=dict['Betrag in Worten']))
    template.Root.Pages.Kids[0].Annots[15].update(pdfrw.PdfDict(V=dict['Betrag in Worten']))
    
    template.Root.Pages.Kids[0].Annots[6].update(pdfrw.PdfDict(V=dict['Zahlung von']))
    template.Root.Pages.Kids[0].Annots[16].update(pdfrw.PdfDict(V=dict['Zahlung von']))
    
    template.Root.Pages.Kids[0].Annots[9].update(pdfrw.PdfDict(V=dict['Kontierung']))
    template.Root.Pages.Kids[0].Annots[19].update(pdfrw.PdfDict(V=dict['Kontierung']))
    



if __name__ == '__main__':
    global check1,check2
    root = Tk()
    ents = makeform(root, fields)
    b1 = Button(root, text='Rechnungen erstellen',
           command=(lambda e=ents: createPDF(e)))
    b1.pack(side=LEFT, padx=5, pady=5)
    b2 = Button(root, text='Quit', command=root.quit)
    b2.pack(side=LEFT, padx=5, pady=5)
    check1 = IntVar()
    c1 = Checkbutton(root,text='Ganzes Jahr?', variable=check1)
    c1.pack(side=LEFT,padx=5,pady=5)
    
   
    root.mainloop()

