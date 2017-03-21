import os, sys

#Image manipulation
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

#Check input format
import mmap

#XML parsing
import xml.etree.ElementTree

#HTML parsing
from lxml import html
import requests

import scraper, config
from globals import Card, specmana

#ensure that mana costs greater than 9 (Kozilek, Emrakul...) aren't misaligned
adjustcmc = False
check9 = '0123456'

def GenerateCMC(name, set):
    global adjustcmc
    diskcost = cost.strip().replace('*', '_').replace('/','-')
#    lookupCMC = os.path.join('CmcCache', '{cost}.png'.format(cost=diskcost))
    lookupCMC = os.path.join('CmcCache', '{cost}.png'.format(cost=diskcost))
    if os.path.exists(lookupCMC):
        tap0 = Image.open(lookupCMC)
        if tap0.mode != 'RGBA':
            tap0 = tap0.convert('RGBA')
        cmc.paste(tap0, (0,0), mask=tap0)
        #still need to check cost adjustment...
        for n in range(len(cost)-1):
            if (cost[n] == '1') and (check9.find(cost[n+1]) != -1):
                adjustcmc = True
    else:
        greaterthan9 = False
        for n in range(len(cost)-1):
            #reset the large mana cost markers
            if greaterthan9:
                greaterthan9 = False
                adjustcmc = True
                continue
            #lands have no mana cost and are tagged with '*'
            if cost[n] == "*":
                continue
            #add correct treatment of separation for split cards
            elif cost[n] == '/':
                symbol = 'Mana/Mana_spn.png'
                tap0 = Image.open(symbol)
                if tap0.mode != 'RGBA':
                    tap0 = tap0.convert('RGBA')

                tap = tap0.resize((16,16))
                cmc.paste(tap, (15*n,0), mask=tap)
            else:
                if (cost[n] == '1') and (check9.find(cost[n+1]) != -1):
                    finalcost = cost[n]+cost[n+1]
                    greaterthan9 = True
                else:
                    finalcost = cost[n]
                symbol = 'Mana/Mana_'+finalcost+'.png'

                tap0 = Image.open(symbol)
                if tap0.mode != 'RGBA':
                    tap0 = tap0.convert('RGBA')

                tap = tap0.resize((16,16))
                cmc.paste(tap, (15*n,0), mask=tap)
        cmc.save((lookupCMC).replace('che-','che/'))

ncount = 0
ncountMB = 0
ncountSB = 0
nstep = 1

if not os.path.exists('./Scans'):
    os.mkdir('./Scans')
if not os.path.exists('./CmcCache'):
    os.mkdir('./CmcCache')

#some position initialization
xtop = 8
xbot = 304
ytop = 11.5
ybot = 45.25

xtopPKMN = 8
xbotPKMN = 237
ytopPKMN = 11.5
ybotPKMN = 45.25

#load the MTG text fonts
fnt = ImageFont.truetype("beleren-webfonts/belerensmallcaps-bold-webfont.ttf", 14)
fnt_title = ImageFont.truetype("beleren-webfonts/belerensmallcaps-bold-webfont.ttf", 18)

#load the PKMN text fonts
pokefnt = ImageFont.truetype("humanist-webfonts/ufonts.com_humanist521bt-ultrabold-opentype.otf", 10)

pokefnt_title = ImageFont.truetype("humanist-webfonts/ufonts.com_humanist521bt-ultrabold-opentype.otf", 14)

#check the input format
isXML = False
isPokemon = False
isHexTCG = False
isMTG = True #default setting is Magic: the Gathering decklist

#Hex TCG specific variables
HexChampion = {}
HexMercenary = {}
HexCards = {}

hexfnt = ImageFont.truetype("agane-webfonts/Agane-55-roman.ttf", 14)
hexfnt_title = ImageFont.truetype("agane-webfonts/Agane-55-roman.ttf", 16)

# create a horizontal gradient...
Hexgradient = Image.new('L', (1,255))

#map the gradient
for x in range(64):
    Hexgradient.putpixel((0,x),254)
for x in range(64):
    Hexgradient.putpixel((0,64+x),254-x)
for x in range(128):
    Hexgradient.putpixel((0,127+x),190-int(1.5*x))

# create a horizontal gradient...
gradient = Image.new('L', (255,1))

#map the gradient
#for x in range(64):
#    gradient.putpixel((x,0),254)
#for x in range(64):
#    gradient.putpixel((63+x,0),max(254-x,0))
#for x in range(128):
#    gradient.putpixel((127+x,0),max(int(190-1.5*x),0))
for x in range(128):
    gradient.putpixel((x,0),int(1.5*x))
for x in range(64):
    gradient.putpixel((127+x,0),190+x)
for x in range(64):
    gradient.putpixel((190+x,0),254)

#check if we should include the sideboard
isSideboard = 0
if len(sys.argv) == 2:
    doSideboard = config.Get('options', 'display_sideboard')
else:
    if str(sys.argv[2]) in ['sb', 'sideboard']:
        doSideboard = True
    elif str(sys.argv[2]) in ['nosb']:
        doSideboard = False
    else: 
        doSideboard = config.Get('options', 'display_sideboard')

#open user input decklist
decklist1 = open(str(sys.argv[1]), 'r')

#determine if input decklist is in XML format
isDeckXML = mmap.mmap(decklist1.fileno(), 0, access=mmap.ACCESS_READ)
if isDeckXML.find('xml') != -1:
    print('Warning - input decklist is in XML format')
    isXML = True

#check for readable content
if isXML:

    info = xml.etree.ElementTree.parse(str(sys.argv[1])).getroot()

    modoformat = {}
    modoformatSB = {}

    for atype in info.findall('Cards'):
        if atype.get('Sideboard') == "true":
            if not doSideboard:
                continue
            else:
                if atype.get('Name') in modoformatSB:
                    modoformatSB[atype.get('Name').replace(' / ',' // ')] += int(atype.get('Quantity'))
                else:
                    modoformatSB[atype.get('Name').replace(' / ',' // ')] = int(atype.get('Quantity'))
        else:
            if atype.get('Name') in modoformat:
                modoformat[atype.get('Name')] += int(atype.get('Quantity'))
            else:
                modoformat[atype.get('Name')] = int(atype.get('Quantity'))

    modonames = [x.replace(' / ',' // ') for x in list(modoformat.keys())]
    modoquant = [modoformat[x] for x in modonames]
    ncountMB = len(modonames)
    modonamesSB = [x.replace(' / ',' // ') for x in list(modoformatSB.keys())]
    modoquantSB = [modoformatSB[x] for x in modonamesSB]
    ncountSB = len(modonamesSB)
    print ncountMB, modonames, modoquant
    print ncountSB, modonamesSB, modoquantSB
    ncount=ncountMB+ncountSB+1 #1 extra space for the sideboard marker
    
else:

    for lines1 in decklist1:
    
        if lines1.lower().find('champion:') != -1 or lines1.lower().find('mercenary:') != -1:

            isHexTCG = True
            isMTG = False

            listChampions = open(os.path.join('.','HexLists','HexList-Champion.dat'), 'r')
            for line in listChampions:
                HexChampion[line.split('.jpg ')[1][:-1]] = line.split('.jpg ')[0]
            listChampions.close()

            listMercenaries = open(os.path.join('.','HexLists','HexList-Mercenary.dat'), 'r')
            for line in listMercenaries:
                HexMercenary[line.split('.jpg ')[1][:-1]] = line.split('.jpg ')[0]
            listMercenaries.close()
    
            listCards = open(os.path.join('.','HexLists','HexList-AllCards.dat'), 'r')
            for line in listCards:
                HexCards[line.split('.jpg ')[1][:-1]] = line.split('.jpg ')[0]
            listCards.close()
    
            continue

        if isHexTCG:

            if isSideboard == 1:
                continue

            if lines1.lower() in ['\n', '\r\n', 'troops\r\n', 'spells\r\n', 'resources\r\n', 'reserves\r\n']:
                if lines1.lower() == 'reserves\r\n':
                    isSideboard = 1
                    continue
                else:
                    continue

 
            ncount = ncount + 1

        else:

#        if lines1[0] == '#':
            if lines1[0] in ['#', '*']:
                if lines1.lower().find('* pok') != -1:
                    print 'Decklist is for Pokemon TCGO ...'
                    isPokemon = True
                    isMTG = False
                    isSideboard = 0
                continue

            if lines1 in ['\n', '\r\n']:
                if isMTG:
                    isSideboard = 1
                    if not doSideboard:
                        continue

            if (isSideboard == 1) and (not doSideboard):
                continue

            ncount = ncount +1

decklist1.close()

#create a header with the deck's name
if isMTG:
    title = Image.new("RGB", (280,34), "black")
    drawtitle = ImageDraw.Draw(title)
    drawtitle.text((10, 7),os.path.basename(str(sys.argv[1]))[0:-4],(250,250,250), font=fnt_title)
elif isPokemon:
    title = Image.new("RGB", (219,35), "black")
    drawtitle = ImageDraw.Draw(title)
    drawtitle.text((10, 8),os.path.basename(str(sys.argv[1]))[0:-4],(250,250,250), font=pokefnt_title)
elif isHexTCG:
    title = Image.new("RGB", (320,34), "black")
    nametitle = str(sys.argv[1])[0:-4]
    nshard = 0
    for shard in ['[DIAMOND]', '[SAPPHIRE]', '[BLOOD]', '[RUBY]', '[WILD]']:
        #print nametitle,nshard
        if nametitle.find(shard) != -1:
            nametitle = nametitle.replace(shard,'')
            newshard = Image.open(os.path.join('.','Mana',shard+'.png')).resize((20,20))
            title.paste(newshard,(10+nshard*20,7))
            nshard = nshard + 1
    drawtitle = ImageDraw.Draw(title)
    drawtitle.text((15+nshard*20, 12),os.path.basename(nametitle), (250,250,250), font=hexfnt_title)

if doSideboard:
    #create a Sideboard partition
    sideboard = Image.new("RGB", (280,34), "black")
    drawtitle = ImageDraw.Draw(sideboard)
    drawtitle.text((10, 7),"Sideboard",(250,250,250), font=fnt_title)

#define the size of the canvas, incl. space for the title header
if isMTG:
    deckwidth = 280
    deckheight = 34*(ncount+1)
elif isPokemon:
    deckwidth = 219
    deckheight = 35*(ncount+1)
elif isHexTCG:
    deckwidth = 320
    deckheight = 35*(ncount+1)
    
#reset the sideboard marker
isSideboard = 0

deck = Image.new("RGB", (deckwidth, deckheight), "white")

deck.paste(title, (0,0))

#now read the decklist
if isMTG:

    if not isXML:

        #parse an ASCII decklist
        doitFirst = []
        doitLast = []
        doSideMark = []
        doitFirstSB = []
        doitLastSB = []
        sizeFirst = 0
        sizeLast = 0
        sizeMark = 0
        sizeFirstSB = 0
        sizeLastSB = 0

        decklist = open(str(sys.argv[1]), 'r')

        for lines in decklist:
            #necessary for appropriate treatment of the missing mana cost of lands
            isitland = 0
            isitspecland = 0

            if lines[0] == '#':
                continue

            if lines in ['\n', '\r\n']:
                isSideboard = 1
                if not doSideboard:
                    continue
                else:
                    # We're at the Sideboard now.
                    print '-- Sideboard --'
    #                deck.paste(sideboard, (0,34*nstep))
                    doSideMark.append('sideboard')
                    doSideMark.append('sideboard')
                    doSideMark.append('sideboard')
                    doSideMark.append('sideboard')
                    sizeMark = sizeMark + 1
    #                nstep = nstep + 1
                    continue

            if (isSideboard == 1) and (not doSideboard):
                continue

            #this step checks whether a specific art is requested by the user - provided via the set name

            card = scraper.get_card_info(lines)
            if card is None:
                continue
            name = card.name
            set = card.set
            cost = card.cost
            quantity = card.quantity

            if isSideboard == 1:
                if not doSideboard:
                    continue
                else:
                    if cost == "*\n":
                        doitLastSB.append(quantity)
                        doitLastSB.append(name)
                        doitLastSB.append(set)
                        doitLastSB.append(cost)
                        sizeLastSB = sizeLastSB + 1
                    else:
                        doitFirstSB.append(quantity)
                        doitFirstSB.append(name)
                        doitFirstSB.append(set)
                        doitFirstSB.append(cost)
                        sizeFirstSB = sizeFirstSB + 1
            else:
                if cost == "*\n":
                    doitLast.append(quantity)
                    doitLast.append(name)
                    doitLast.append(set)
                    doitLast.append(cost)
                    sizeLast = sizeLast + 1
                else:
                    doitFirst.append(quantity)
                    doitFirst.append(name)
                    doitFirst.append(set)
                    doitFirst.append(cost)
                    sizeFirst = sizeFirst + 1

        doitAll = doitFirst+doitLast
        sizeAll = sizeFirst+sizeLast
        if doSideboard:
            doitAll = doitAll+doSideMark
            sizeAll = sizeAll+sizeMark
            if sizeFirstSB != 0:
                doitAll = doitAll+doitFirstSB
                sizeAll = sizeAll+sizeFirstSB
            if sizeLastSB != 0:
                doitAll = doitAll+doitLastSB
                sizeAll = sizeAll+sizeLastSB
        print "final list to be stacked: ",doitAll,sizeAll

        for nAll in range(sizeAll):
            quantity = doitAll[0+4*nAll]
            name = doitAll[1+4*nAll]
            set = doitAll[2+4*nAll]
            cost = doitAll[3+4*nAll]

            if quantity == 'sideboard':
                deck.paste(sideboard, (0,34*nstep))
                nstep = nstep + 1
                continue

            #all card arts are found on magiccards.info
        #    cmcscan = cmctree.xpath('//a[img]/@href')

            if name.find(" // ") != -1:
                namesplit = name.replace(" // ","/")
                lookupScan = scraper.download_scan(namesplit,set)
            else:
                lookupScan = scraper.download_scan(name,set)

    #        print name, lookupScan

            img = Image.open(lookupScan)
            if name.find(" // ") != -1:
                img = img.rotate(-90)

            #check if im has Alpha band...
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            #resize the gradient to the size of im...
            alpha = gradient.resize(img.size)

            #put alpha in the alpha band of im...
            img.putalpha(alpha)

            bkgd = Image.new("RGB", img.size, "black")
            bkgd.paste(img, (0,0), mask=img)

            cut = bkgd.crop((xtop+12, ytop+125, xbot, ybot+125))

            draw = ImageDraw.Draw(cut)
            #create text outline
            draw.text((6, 6),str(quantity)+'  '+name,(0,0,0), font=fnt)
            draw.text((8, 6),str(quantity)+'  '+name,(0,0,0), font=fnt)
            draw.text((6, 8),str(quantity)+'  '+name,(0,0,0), font=fnt)
            draw.text((8, 8),str(quantity)+'  '+name,(0,0,0), font=fnt)
            #enter text
            draw.text((7, 7),str(quantity)+'  '+name,(250,250,250), font=fnt)

            cmc = Image.new('RGBA',(16*len(cost), 16))

            GenerateCMC(name, set)

            #place the cropped picture of the current card
            deck.paste(cut, (0,34*nstep))

            #adjust cmc size to reflex manacost greater than 9
            if adjustcmc:
                deck.paste(cmc, (280-15*(len(cost)-1),8+34*nstep), mask=cmc)
                adjustcmc = False
            else:
                deck.paste(cmc, (280-15*len(cost),8+34*nstep), mask=cmc)

            nstep = nstep+1

        decklist.close()

    else:

        #parse the XML decklist
        doitFirst = []
        doitLast = []
        doSideMark = []
        doitFirstSB = []
        doitLastSB = []
        sizeFirst = 0
        sizeLast = 0
        sizeMark = 0
        sizeFirstSB = 0
        sizeLastSB = 0

        for n in range(ncountMB):
            #necessary for appropriate treatment of the missing mana cost of lands
            isitland = 0
            isitspecland = 0

            #reset the new parser
            set = None
            scan_part1 = ' '

            name = modonames[n]
            quantity = modoquant[n]

            card = scraper.get_card_info("{q} {n}".format(q=quantity, n=name))
            if card is None:
                continue
            name = card.name
            set = card.set
            cost = card.cost
            quantity = card.quantity

            if cost == "*\n":
                doitLast.append(quantity)
                doitLast.append(name)
                doitLast.append(set)
                doitLast.append(cost)
                sizeLast = sizeLast + 1
            else:
                doitFirst.append(quantity)
                doitFirst.append(name)
                doitFirst.append(set)
                doitFirst.append(cost)
                sizeFirst = sizeFirst + 1

        if ncountSB != 0:

            print '-- Sideboard --'
            doSideMark.append('sideboard')
            doSideMark.append('sideboard')
            doSideMark.append('sideboard')
            doSideMark.append('sideboard')
            sizeMark = sizeMark + 1

            for n in range(ncountSB):

                ncount_card = 0

                #necessary for appropriate treatment of the missing mana cost of lands
                isitland = 0
                isitspecland = 0

                #reset the new parser
                set = ' '
                scan_part1 = ' '

                name = modonamesSB[n]
                quantity = modoquantSB[n]

                card = scraper.get_card_info("{q} {n}".format(q=quantity, n=name))
                if card is None:
                    continue
                name = card.name
                set = card.set
                cost = card.cost
                quantity = card.quantity


                if cost == "*\n":
                    doitLastSB.append(quantity)
                    doitLastSB.append(name)
                    doitLastSB.append(set)
                    doitLastSB.append(cost)
                    sizeLastSB = sizeLastSB + 1
                else:
                    doitFirstSB.append(quantity)
                    doitFirstSB.append(name)
                    doitFirstSB.append(set)
                    doitFirstSB.append(cost)
                    sizeFirstSB = sizeFirstSB + 1

        doitAll = doitFirst+doitLast
        sizeAll = sizeFirst+sizeLast
        if sizeMark != 0:
            doitAll = doitAll+doSideMark
            sizeAll = sizeAll+sizeMark
            if sizeFirstSB != 0:
                doitAll = doitAll+doitFirstSB
                sizeAll = sizeAll+sizeFirstSB
            if sizeLastSB != 0:
                doitAll = doitAll+doitLastSB
                sizeAll = sizeAll+sizeLastSB
        print "final list to be stacked: ",doitAll,sizeAll

        for nAll in range(sizeAll):
            quantity = doitAll[0+4*nAll]
            name = doitAll[1+4*nAll]
            set = doitAll[2+4*nAll]
            cost = doitAll[3+4*nAll]

            print "stacking: ",name

            if quantity == 'sideboard':
                deck.paste(sideboard, (0,34*nstep))
                nstep = nstep + 1
                continue

    #        lookupScan = scraper.download_scan(name, set)
            if name.find(" // ") != -1:
                namesplit = name.replace(" // ","/")
                lookupScan = scraper.download_scan(namesplit,set)
            else:
                lookupScan = scraper.download_scan(name,set)

    #        print name, lookupScan

            img = Image.open(lookupScan)
            if name.find(" // ") != -1:
                img = img.rotate(-90)

            #check if im has Alpha band...
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            #resize the gradient to the size of im...
            alpha = gradient.resize(img.size)

            #put alpha in the alpha band of im...
            img.putalpha(alpha)

            bkgd = Image.new("RGB", img.size, "black")
            bkgd.paste(img, (0,0), mask=img)

            cut = bkgd.crop((xtop+12, ytop+125, xbot, ybot+125))

            draw = ImageDraw.Draw(cut)
            #create text outline
            draw.text((6, 6),str(quantity)+'  '+name,(0,0,0), font=fnt)
            draw.text((8, 6),str(quantity)+'  '+name,(0,0,0), font=fnt)
            draw.text((6, 8),str(quantity)+'  '+name,(0,0,0), font=fnt)
            draw.text((8, 8),str(quantity)+'  '+name,(0,0,0), font=fnt)
            #enter text
            draw.text((7, 7),str(quantity)+'  '+name,(250,250,250), font=fnt)

            cmc = Image.new('RGBA',(16*len(cost), 16))

            GenerateCMC(name, set)

            #place the cropped picture of the current card
            deck.paste(cut, (0,34*nstep))

            #adjust cmc size to reflex manacost greater than 9
            if adjustcmc:
                deck.paste(cmc, (280-15*(len(cost)-1),8+34*nstep), mask=cmc)
                adjustcmc = False
            else:
                deck.paste(cmc, (280-15*len(cost),8+34*nstep), mask=cmc)

            nstep = nstep+1

elif isPokemon:

    decklist = open(str(sys.argv[1]), 'r')

    for lines in decklist:

        if lines[0].isdigit():
            data = lines.split(' ')
            data[-1] = data[-1][:-1]

            quantity = data[0]
            set = data[-2]
            setID = data[-1]
            name = data[1]+' '

            for item in data[2:-2]:
                name += item+' '

            lookupScan,displayname = scraper.download_scanPKMN(name,set,setID)
            print displayname, set, setID
            
            img = Image.open(lookupScan)

            #check if im has Alpha band...
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            #resize the gradient to the size of im...
            alpha = gradient.resize(img.size)

            #put alpha in the alpha band of im...
            img.putalpha(alpha)

            bkgd = Image.new("RGB", img.size, "black")
            bkgd.paste(img, (0,0), mask=img)

            cut = bkgd.crop((xtopPKMN, ytopPKMN+90, xbotPKMN-10, ybotPKMN+100))
            cut = cut.resize((deckwidth,34))

            draw = ImageDraw.Draw(cut)
            #create text outline
            draw.text((6, 11),str(quantity)+'  '+displayname,(0,0,0), font=pokefnt)
            draw.text((8, 11),str(quantity)+'  '+displayname,(0,0,0), font=pokefnt)
            draw.text((6, 13),str(quantity)+'  '+displayname,(0,0,0), font=pokefnt)
            draw.text((8, 13),str(quantity)+'  '+displayname,(0,0,0), font=pokefnt)
            #enter text
            draw.text((7, 12),str(quantity)+'  '+displayname,(250,250,250), font=pokefnt)

            #place the cropped picture of the current card
            deck.paste(cut, (0,35*nstep))

            nstep = nstep+1

    decklist.close()

elif isHexTCG:

    banner = Image.new("RGB", (deckheight-35, 50), "black")

    decklist = open(str(sys.argv[1]), 'r')

    for lines in decklist:

        if isSideboard == 1:
            continue

        if lines.lower().find('champion:') != -1 or lines.lower().find('mercenary:') != -1:

            drawbanner = ImageDraw.Draw(banner)
            drawbanner.text((15,15), str(lines), (250,250,250), font=hexfnt_title)

            data = lines.split(': ')
            #mainguy = data[1][:-2]
            mainguy = data[1].replace('\r','').replace('\n','')
            if data[0].lower() == 'champion':
                typeCM = 'C'
                mainguyscan = HexChampion[mainguy]
            else:
                typeCM = 'M'
                mainguyscan = HexMercenary[mainguy]
            #print mainguy,mainguyscan

            lookupScan = scraper.download_scanHexCM(mainguy,mainguyscan,typeCM)

            mainguyImg = Image.open(lookupScan)
            mainguycut = mainguyImg.crop((135,55,185,275))

            banner = banner.rotate(90, expand=True)

            #check if im has Alpha band...
            if mainguycut.mode != 'RGBA':
                mainguycut = mainguycut.convert('RGBA')

            #resize the gradient to the size of im...
            alpha = Hexgradient.resize(mainguycut.size)

            #put alpha in the alpha band of im...
            mainguycut.putalpha(alpha)

            banner.paste(mainguycut, (0,0), mask=mainguycut)

            deck.paste(banner, (0,35))

        elif lines.lower() in ['\n', '\r\n', 'troops\r\n', 'spells\r\n', 'resources\r\n', 'reserves\r\n']:

            if lines.lower() == 'reserves\r\n':
                isSideboard = 1
                continue
            else:
                continue

        else:

            data = lines.split('x ')
            quantity = data[0]
            #name = data[1][:-2]
            name = data[1].replace('\r','').replace('\n','')
            namescan = HexCards[name]
            #print quantity,name,namescan

            lookupScan = scraper.download_scanHex(name,namescan)
            
            img = Image.open(lookupScan)
            img = img.crop((39,130,309,164))

            #resize the gradient to the size of im...
            alpha = gradient.resize(img.size)

            #put alpha in the alpha band of im...
            img.putalpha(alpha)

            bkgd = Image.new("RGB", img.size, "black")
            bkgd.paste(img, (0,0), mask=img)

            cut = bkgd

            draw = ImageDraw.Draw(cut)
            #create text outline
            draw.text((6, 6),str(quantity)+'  '+name,(0,0,0), font=hexfnt)
            draw.text((8, 6),str(quantity)+'  '+name,(0,0,0), font=hexfnt)
            draw.text((6, 8),str(quantity)+'  '+name,(0,0,0), font=hexfnt)
            draw.text((8, 8),str(quantity)+'  '+name,(0,0,0), font=hexfnt)
            #enter text
            draw.text((7, 7),str(quantity)+'  '+name,(250,250,250), font=hexfnt)

            deck.paste(cut, (50,35*nstep))

            nstep = nstep + 1

    decklist.close()
            
if isMTG:
    deck = deck.crop((0, 0, deckwidth-10, deckheight))
elif isPokemon:
    deck = deck.crop((0, 0, deckwidth-10, 35*nstep))
elif isHexTCG:
    deck = deck.crop((0, 0, deckwidth-22, deckheight))
    
deck.save(str(sys.argv[1])[0:-4]+".png")
altpath = config.Get('options', 'output_path')
if altpath is not None:
    deck.save(altpath)
