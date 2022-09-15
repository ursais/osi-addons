# -*- encoding: utf-8 -*-

import xlwt


def font_style(position='left',bold=0, fontos=0, font_height=200,border=0,color=False):
    font = xlwt.Font()
    font.name = 'Verdana'
    font.bold = bold
    font.height=font_height
    center = xlwt.Alignment()
    center.horz = xlwt.Alignment.HORZ_CENTER
    center.vert = xlwt.Alignment.VERT_CENTER
    center.wrap = xlwt.Alignment.VERT_JUSTIFIED

    left = xlwt.Alignment()
    left.horz = xlwt.Alignment.HORZ_LEFT
    left.vert = xlwt.Alignment.VERT_CENTER
    left.wrap = xlwt.Alignment.VERT_JUSTIFIED

    right = xlwt.Alignment()
    right.horz = xlwt.Alignment.HORZ_RIGHT
    right.vert = xlwt.Alignment.VERT_CENTER
    right.wrap = xlwt.Alignment.VERT_JUSTIFIED

    borders = xlwt.Borders()
    borders.right = 1
    borders.left=1
    borders.top = 1
    borders.bottom = 1
    
    orient = xlwt.Alignment()
    orient.orie = xlwt.Alignment.ORIENTATION_90_CC
    
    style = xlwt.XFStyle()
    
    if border == 1:
        style.borders = borders
    
    if fontos == 'red' :
        font.colour_index = 2
        style.font = font
    if fontos == 'purple_ega' :
        font.colour_index = 0x14
        style.font = font
    else: style.font = font

    if position == 'center' :
        style.alignment = center
    elif position == 'right':
        style.alignment = right
    else : 
        style.alignment = left
    if color =='grey':
        badBG = xlwt.Pattern()
        badBG.pattern = badBG.SOLID_PATTERN 
        badBG.pattern_fore_colour = 22
        style.pattern = badBG
    if color =='red':
        badBG = xlwt.Pattern()
        badBG.pattern = badBG.SOLID_PATTERN 
        badBG.pattern_fore_colour = 5
        style.pattern = badBG
        
    if color =='yellow':
        badBG = xlwt.Pattern()
        badBG.pattern = badBG.SOLID_PATTERN 
        badBG.pattern_fore_colour = 0x0D
        style.pattern = badBG

    if color =='purple':
        badBG = xlwt.Pattern()
        badBG.pattern = badBG.SOLID_PATTERN 
        badBG.pattern_fore_colour = 0x14
        style.pattern = badBG

    return style
