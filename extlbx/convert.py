# coding=utf-8
"""
CONVERT
Convierte los archivos y exporta versiones.

Autor: PABLO PIZARRO @ github.com/ppizarror
Fecha: 2017
Licencia: MIT
"""

# Importación de librerías
from __future__ import print_function
from latex import *
from releases import RELEASES
from stats import *
from subprocess import call
from version import *
from ziputils import *
import copy
import pyperclip
import time

# Constantes
CREATE_NO_WINDOW = 0x08000000
MSG_DCOMPILE = 'COMPILANDO ... '
MSG_FOKTIMER = 'OK [t {0:.3g}]'
MSG_GEN_FILE = 'GENERANDO ARCHIVOS ... '
MSG_LAST_VER = 'ULTIMA VERSION:\t {0}'
MSG_UPV_FILE = 'ACTUALIZANDO VERSION ...'


# noinspection PyUnusedLocal
def nonprint(arg, *args, **kwargs):
    """
    Desactiva el printing.

    :param arg:
    :param args:
    :param kwargs:
    :return:
    """
    pass


# noinspection PyBroadException
def export_informe(version, versiondev, versionhash, printfun=print, dosave=True, docompile=True,
                   addwhitespace=False, deletecoments=True, plotstats=True, doclean=False):
    """
    Exporta el archivo principal, actualiza version.

    :param addwhitespace: Añade espacios en blanco al comprimir archivos
    :param deletecoments: Borra comentarios
    :param doclean: Limpia el diccionario
    :param docompile: Compila automáticamente
    :param dosave: Guarda o no los archivos
    :param plotstats: Plotea las estadísticas
    :param printfun: Función que imprime en consola
    :param version: Versión
    :param versiondev: Versión developer
    :param versionhash: Hash de la versión
    :return:
    """

    # Tipo release
    release = RELEASES['_INFORME']

    # Obtiene archivos
    configfile = release['CONFIGFILE']
    examplefile = release['EXAMPLEFILE']
    filedelcoments = release['FILEDELCOMENTS']
    files = release['FILES']
    filestrip = release['FILESTRIP']
    initconffile = release['INITCONFFILE']
    mainfile = release['MAINFILE']
    mainsinglefile = release['SINGLEFILE']
    stat = release['STATS']

    # Constantes
    main_data = open(mainfile)
    main_data.read()
    initdocumentline = find_line(main_data, '\\usepackage[utf8]{inputenc}') + 1
    codetablewidthpos = find_line(main_data, '\\begin{minipage}{0.976\\textwidth}')
    headersize = find_line(main_data, '% Licencia MIT:') + 2
    headerversionpos = find_line(main_data, '% Versión:      ')
    itableoriginal = '0.976\\textwidth'
    itablenew = '1.0126\\textwidth'
    versionheader = '% Versión:      {0} ({1})\n'
    main_data.close()

    # Se obtiene el día
    dia = time.strftime('%d/%m/%Y')

    # Se crea el header de la versión
    versionhead = versionheader.format(version, dia)

    # Se buscan números de lineas de hyperref
    initconf_data = open(initconffile)
    initconf_data.read()
    l_tdate, d_tdate = find_line(initconf_data, 'Template.Fecha', True)
    l_thash, d_thash = find_line(initconf_data, 'Template.Version.Hash', True)
    l_ttype, d_ttype = find_line(initconf_data, 'Template.Tipo', True)
    l_tvdev, d_tvdev = find_line(initconf_data, 'Template.Version.Dev', True)
    l_tvrel, d_tvrel = find_line(initconf_data, 'Template.Version.Release', True)
    l_vcmtd, d_vcmtd = find_line(initconf_data, 'pdfproducer', True)
    initconf_data.close()

    # Se actualizan líneas de hyperref
    d_tdate = replace_argument(d_tdate, 1, dia)
    d_thash = replace_argument(d_thash, 1, versionhash)
    d_ttype = replace_argument(d_ttype, 1, 'Normal')
    d_tvdev = replace_argument(d_tvdev, 1, versiondev + '-N')
    d_tvrel = replace_argument(d_tvrel, 1, version)
    d_vcmtd = replace_argument(d_vcmtd, 1, release['VERLINE'].format(version))

    # Carga los archivos y cambian las versiones
    t = time.time()
    if dosave:
        printfun(MSG_GEN_FILE, end='')
    else:
        printfun(MSG_UPV_FILE, end='')
    for f in files.keys():
        data = files[f]
        # noinspection PyBroadException
        try:
            fl = open(f)
            for line in fl:
                data.append(line)
            fl.close()
        except:
            printfun('Error al cargar el archivo {0}'.format(f))

        # Se cambia la versión
        data[headerversionpos] = versionhead

        # Se actualiza la versión en initconf
        if f == initconffile:
            data[l_tdate] = d_tdate
            data[l_thash] = d_thash
            data[l_ttype] = d_ttype
            data[l_tvdev] = d_tvdev
            data[l_tvrel] = d_tvrel
            data[l_vcmtd] = d_vcmtd

        # Se reescribe el archivo
        if dosave:
            newfl = open(f, 'w')
            for j in data:
                newfl.write(j)
            newfl.close()

    # Se obtiene la cantidad de líneas de código
    lc = 0
    for f in files.keys():
        lc += len(files[f])

    # Se modifican propiedades para establecer tipo compacto
    data = files[initconffile]
    d_ttype = replace_argument(d_ttype, 1, 'Compacto')
    d_tvdev = replace_argument(d_tvdev, 1, versiondev + '-C')
    data[l_thash] = d_thash
    data[l_ttype] = d_ttype
    data[l_tvdev] = d_tvdev

    # Se crea ejemplo generado automáticamente
    fl = open(release['EXAMPLECLONE'], 'w')
    data = files[examplefile]
    for k in data:
        fl.write(k)
    fl.close()

    # Se crea el archivo unificado
    fl = open(mainsinglefile, 'w')
    data = files[mainfile]
    data.pop(1)  # Se elimina el tipo de documento del header
    data.insert(1, '% Advertencia:  Documento generado automáticamente a partir del main.tex y\n%               los '
                   'archivos .tex de la carpeta lib/\n')
    data[codetablewidthpos] = data[codetablewidthpos].replace(itableoriginal, itablenew)
    line = 0
    stconfig = False  # Indica si se han escrito comentarios en configuraciones

    # Se recorren las líneas del archivo
    for d in data:
        write = True
        if line < initdocumentline:
            fl.write(d)
            write = False
        # Si es una línea en blanco se agrega
        if d == '\n' and write:
            fl.write(d)
        else:
            # Si es un import pega el contenido
            try:
                if d[0:6] == '\input':
                    libr = d.replace('\input{', '').replace('}', '').strip()
                    libr = libr.split(' ')[0]
                    if '.tex' not in libr:
                        libr += '.tex'
                    if libr != examplefile:

                        # Se escribe desde el largo del header en adelante
                        libdata = files[libr]  # Datos del import
                        libstirp = filestrip[libr]  # Eliminar espacios en blanco
                        libdelcom = filedelcoments[libr]  # Borrar comentarios

                        for libdatapos in range(headersize, len(libdata)):
                            srclin = libdata[libdatapos]

                            # Se borran los comentarios
                            if deletecoments and libdelcom:
                                if '%' in srclin:
                                    if libr == configfile:
                                        if srclin.upper() == srclin:
                                            if stconfig:
                                                fl.write('\n')
                                            fl.write(srclin)
                                            stconfig = True
                                            continue
                                    comments = srclin.strip().split('%')
                                    if comments[0] is '':
                                        srclin = ''
                                    else:
                                        srclin = srclin.replace('%' + comments[1], '')
                                        if libdatapos != len(libdata) - 1:
                                            srclin = srclin.strip() + '\n'
                                        else:
                                            srclin = srclin.strip()
                                elif srclin.strip() is '':
                                    srclin = ''
                            else:
                                if libr == configfile:
                                    try:
                                        if libdata[libdatapos + 1][0] == '%' and srclin.strip() is '':
                                            srclin = ''
                                    except:
                                        pass

                            # Se ecribe la línea
                            if srclin is not '':
                                # Se aplica strip dependiendo del archivo
                                if libstirp:
                                    fl.write(srclin.strip())
                                else:
                                    fl.write(srclin)

                        fl.write('\n')  # Se agrega espacio vacío
                    else:
                        fl.write(d.replace('lib/', ''))
                    write = False
            except:
                pass

            # Se agrega un espacio en blanco a la página después del comentario
            if line >= initdocumentline and write:
                if d[0:2] == '% ' and d[3] != ' ' and d != '% CONFIGURACIONES\n':
                    if d != '% FIN DEL DOCUMENTO\n' and addwhitespace:
                        fl.write('\n')
                        pass
                    d = d.replace('IMPORTACIÓN', 'DECLARACIÓN')
                    if d == '% RESUMEN O ABSTRACT\n':
                        d = '% ======================= RESUMEN O ABSTRACT =======================\n'
                    fl.write(d)
                elif d == '% CONFIGURACIONES\n':
                    pass
                else:
                    fl.write(d)

        # Aumenta la línea
        line += 1

    printfun(MSG_FOKTIMER.format(time.time() - t))
    fl.close()

    # Compila el archivo
    if docompile and dosave:
        t = time.time()
        with open(os.devnull, 'w') as FNULL:
            printfun(MSG_DCOMPILE, end='')

            call(['pdflatex', mainsinglefile], stdout=FNULL, creationflags=CREATE_NO_WINDOW)
            t1 = time.time() - t
            call(['pdflatex', mainsinglefile], stdout=FNULL, creationflags=CREATE_NO_WINDOW)
            t2 = time.time() - t
            tmean = (t1 + t2) / 2
            printfun(MSG_FOKTIMER.format(tmean))

        # Se agregan las estadísticas
        add_stat(stat['FILE'], versiondev, tmean, dia, lc, versionhash)

        # Se plotean las estadísticas
        if plotstats:
            plot_stats(stat['FILE'], stat['CTIME'], stat['LCODE'])

    # Se exporta el proyecto normal
    if dosave:
        czip = release['ZIP']['NORMAL']
        export_normal = Zip(czip['FILE'])
        export_normal.add_excepted_file(czip['EXCEPTED'])
        export_normal.add_file(czip['ADD']['FILES'])
        export_normal.add_folder(czip['ADD']['FOLDER'])
        export_normal.save()

        # Se exporta el proyecto único
        czip = release['ZIP']['COMPACT']
        export_single = Zip(czip['FILE'])
        export_single.add_file(czip['ADD']['FILES'], 'lib/')
        export_single.add_folder(czip['ADD']['FOLDER'])
        export_single.save()

    try:
        pyperclip.copy('Version ' + versiondev)
    except:
        pass

    if doclean:
        clear_dict(RELEASES['_INFORME'], 'FILES')

    return


def export_auxiliares(version, versiondev, versionhash, printfun=print, dosave=True, docompile=True,
                      addwhitespace=False, deletecoments=True, plotstats=True):
    """
    Exporta las auxiliares.

    :param addwhitespace: Añade espacios en blanco al comprimir archivos
    :param deletecoments: Borra comentarios
    :param docompile: Compila automáticamente
    :param dosave: Guarda o no los archivos
    :param plotstats: Plotea las estadísticas
    :param printfun: Función que imprime en consola
    :param version: Versión
    :param versiondev: Versión developer
    :param versionhash: Hash de la versión
    :return:
    """

    # Tipo release
    release = RELEASES['AUXILIAR']

    # Obtiene archivos
    t = time.time()

    # Genera informe
    # noinspection PyTypeChecker
    export_informe(version, versiondev, versionhash, dosave=False, docompile=False,
                   plotstats=False, addwhitespace=addwhitespace, deletecoments=deletecoments,
                   printfun=nonprint)

    if dosave:
        printfun(MSG_GEN_FILE, end='')
    else:
        printfun(MSG_UPV_FILE, end='')
    mainf = RELEASES['_INFORME']['FILES']
    files = release['FILES']
    files['main.tex'] = copy.copy(mainf['main.tex'])
    files['lib/function/core.tex'] = copy.copy(mainf['lib/function/core.tex'])
    files['lib/function/elements.tex'] = copy.copy(mainf['lib/function/elements.tex'])
    files['lib/function/equation.tex'] = copy.copy(mainf['lib/function/equation.tex'])
    files['lib/function/image.tex'] = copy.copy(mainf['lib/function/image.tex'])
    files['lib/function/title.tex'] = file_to_list('lib/function/auxiliar_title.tex')
    files['lib/function/auxiliar.tex'] = file_to_list('lib/function/auxiliar.tex')
    files['lib/example.tex'] = file_to_list('lib/auxiliar_example.tex')
    files['lib/initconf.tex'] = copy.copy(mainf['lib/initconf.tex'])
    files['lib/config.tex'] = copy.copy(mainf['lib/config.tex'])
    files['lib/pageconf.tex'] = copy.copy(mainf['lib/pageconf.tex'])
    files['lib/styles.tex'] = copy.copy(mainf['lib/styles.tex'])
    files['lib/imports.tex'] = copy.copy(mainf['lib/imports.tex'])
    filedelcoments = release['FILEDELCOMENTS']
    filestrip = release['FILESTRIP']
    mainfile = release['MAINFILE']
    subrelfile = release['SUBRELFILES']
    examplefile = release['EXAMPLEFILE']
    subrlfolder = release['ROOT']
    stat = release['STATS']
    configfile = release['CONFIGFILE']

    # Constantes
    main_data = open(mainfile)
    main_data.read()
    initdocumentline = find_line(main_data, '\\usepackage[utf8]{inputenc}') + 1
    headersize = find_line(main_data, '% Licencia MIT:') + 2
    headerversionpos = find_line(main_data, '% Versión:      ')
    versionhead = '% Versión:      {0} ({1})\n'
    main_data.close()

    # Se obtiene el día
    dia = time.strftime('%d/%m/%Y')

    # Se crea el header
    versionhead = versionhead.format(version, dia)

    # MODIFICA EL MAIN
    main_auxiliar = file_to_list(subrelfile['MAIN'])
    ia, ja = find_block(main_auxiliar, '\def\equipodocente')
    nb = extract_block_from_list(main_auxiliar, ia, ja)
    nb.append('\n')
    i, j = find_block(files[mainfile], '\def\\tablaintegrantes')
    files[mainfile] = replace_block_from_list(files[mainfile], nb, i, j)
    files[mainfile][1] = '% Documento:    Archivo principal\n'
    ra, rb = find_block(files[mainfile], '% PORTADA', True)
    files[mainfile] = del_block_from_list(files[mainfile], ra, rb)
    ra, rb = find_block(files[mainfile], '% RESUMEN O ABSTRACT', True)
    files[mainfile] = del_block_from_list(files[mainfile], ra, rb)
    ra, rb = find_block(files[mainfile], '% TABLA DE CONTENIDOS - ÍNDICE', True)
    files[mainfile] = del_block_from_list(files[mainfile], ra, rb)
    ra, rb = find_block(files[mainfile], '% IMPORTACIÓN DE ENTORNOS', True)
    files[mainfile] = del_block_from_list(files[mainfile], ra, rb)
    ra, rb = find_block(files[mainfile], '% CONFIGURACIONES FINALES', True)
    files[mainfile] = del_block_from_list(files[mainfile], ra, rb)
    ra, rb = find_block(files[mainfile], 'nombredelinforme')
    files[mainfile][ra] = '\def\\tituloauxiliar {Título de la auxiliar}\n'
    ra, rb = find_block(files[mainfile], 'temaatratar')
    files[mainfile][ra] = '\def\\temaatratar {Tema de la auxiliar}\n'
    i1, f1 = find_block(main_auxiliar, '% IMPORTACIÓN DE FUNCIONES', True)
    nl = extract_block_from_list(main_auxiliar, i1, f1)
    i2, f2 = find_block(files[mainfile], '% IMPORTACIÓN DE FUNCIONES', True)
    files[mainfile] = replace_block_from_list(files[mainfile], nl, i2, f2 - 1)
    files[mainfile][len(files[mainfile]) - 1] = files[mainfile][len(files[mainfile]) - 1].strip()

    # MODIFICA CONFIGURACIIONES
    fl = release['CONFIGFILE']
    cdel = ['addemptypagetwosides', 'nomlttable', 'nomltsrc', 'nomltfigure',
            'nomltcont', 'nameportraitpage', 'nameabstract', 'indextitlecolor',
            'portraittitlecolor', 'fontsizetitlei', 'styletitlei',
            'firstpagemargintop', 'romanpageuppercase']
    for cdel in cdel:
        ra, rb = find_block(files[fl], cdel, True)
        files[fl].pop(ra)
    ra, rb = find_block(files[fl], '% CONFIGURACIÓN DEL ÍNDICE', True)
    files[fl] = del_block_from_list(files[fl], ra - 1, rb)
    ra, rb = find_block(files[fl], '% CONFIGURACIÓN PORTADA Y HEADERS', True)
    files[fl] = del_block_from_list(files[fl], ra - 1, rb)
    for cdel in ['namereferences', 'nomltwsrc', 'nomltwfigure', 'nomltwtable']:
        ra, rb = find_block(files[fl], cdel, True)
        files[fl][ra] = files[fl][ra].replace('    %', '%')
    ra, rb = find_block(files[fl], 'showdotontitles', True)
    nconf = replace_argument(files[fl][ra], 1, 'false').replace(' %', '%')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'pagemargintop', True)
    nconf = replace_argument(files[fl][ra], 1, '2.30').replace(' %', '%')
    files[fl][ra] = nconf
    files[fl][len(files[fl]) - 1] = files[fl][len(files[fl]) - 1].strip()

    # CAMBIA IMPORTS
    fl = release['IMPORTSFILE']
    idel = ['usepackage{notoccite}']
    for idel in idel:
        ra, rb = find_block(files[fl], idel, True)
        files[fl].pop(ra)
    files[fl][len(files[fl]) - 1] = files[fl][len(files[fl]) - 1].strip()

    # CAMBIO INITCONF
    fl = release['INITCONFFILE']
    ra, _ = find_block(files[fl], '\checkvardefined{\\nombredelinforme}')
    files[fl][ra] = '\checkvardefined{\\tituloauxiliar}\n'
    ra, _ = find_block(files[fl], '\g@addto@macro\\nombredelinforme\\xspace')
    files[fl][ra] = '\t\g@addto@macro\\tituloauxiliar\\xspace\n'
    ra, _ = find_block(files[fl], '\ifthenelse{\isundefined{\\tablaintegrantes}}{')
    files[fl][ra] = '\ifthenelse{\isundefined{\\equipodocente}}{\n'
    ra, _ = find_block(files[fl], '\errmessage{LaTeX Warning: Se borro la variable \\noexpand\\tablaintegrantes, '
                                  'creando una vacia}')
    files[fl][ra] = '\t\errmessage{LaTeX Warning: Se borro la variable \\noexpand\\equipodocente, creando una vacia}\n'
    ra, _ = find_block(files[fl], '\def\\tablaintegrantes {}')
    files[fl][ra] = '\t\def\\equipodocente {}\n'
    ra, _ = find_block(files[fl], 'Template.Nombre')
    files[fl][ra] = replace_argument(files[fl][ra], 1, 'Template-Auxiliares')
    ra, _ = find_block(files[fl], 'Template.Version.Dev')
    files[fl][ra] = replace_argument(files[fl][ra], 1, versiondev + '-AUX-N')
    ra, _ = find_block(files[fl], 'Template.Tipo')
    files[fl][ra] = replace_argument(files[fl][ra], 1, 'Normal')
    ra, _ = find_block(files[fl], 'Template.Web.Dev')
    files[fl][ra] = replace_argument(files[fl][ra], 1, 'https://github.com/ppizarror/Template-Auxiliares/')
    ra, _ = find_block(files[fl], 'Documento.Titulo')
    files[fl][ra] = replace_argument(files[fl][ra], 1, '\\tituloauxiliar')
    ra, _ = find_block(files[fl], 'pdftitle')
    files[fl][ra] = replace_argument(files[fl][ra], 1, '\\tituloauxiliar')
    ra, _ = find_block(files[fl], 'Template.Web.Manual')
    files[fl][ra] = replace_argument(files[fl][ra], 1, 'http://ppizarror.com/Template-Auxiliares/')
    ra, _ = find_block(files[fl], 'pdfproducer')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['VERLINE'].format(version))
    files[fl][len(files[fl]) - 1] = files[fl][len(files[fl]) - 1].strip()

    # PAGECONF
    fl = release['PAGECONFFILE']
    aux_pageconf = file_to_list(subrelfile['PAGECONF'])
    i1, f1 = find_block(aux_pageconf, '% Numeración de páginas', True)
    nl = extract_block_from_list(aux_pageconf, i1, f1)
    i2, f2 = find_block(files[fl], '% Numeración de páginas', True)
    files[fl] = replace_block_from_list(files[fl], nl, i2, f2 - 1)
    i1, f1 = find_block(aux_pageconf, '% Márgenes de páginas y tablas', True)
    nl = extract_block_from_list(aux_pageconf, i1, f1)
    i2, f2 = find_block(files[fl], '% Márgenes de páginas y tablas', True)
    files[fl] = replace_block_from_list(files[fl], nl, i2, f2 - 1)
    i1, f1 = find_block(aux_pageconf, '% Se crean los header-footer', True)
    nl = extract_block_from_list(aux_pageconf, i1, f1)
    i2, f2 = find_block(files[fl], '% Se crean los header-footer', True)
    files[fl] = replace_block_from_list(files[fl], nl, i2, f2 - 1)
    ra, _ = find_block(files[fl], '% Profundidad del índice')
    i1, f1 = find_block(aux_pageconf, '% Tamaño fuentes', True)
    nl = extract_block_from_list(aux_pageconf, i1, f1)
    for i in range(1):
        files[fl].pop()
    files[fl] = add_block_from_list(files[fl], nl, len(files[fl]) - 1)
    pcfg = ['listfigurename', 'listtablename', 'contentsname', 'lstlistlistingname']
    for pcfg in pcfg:
        ra, _ = find_block(files[fl], pcfg)
    files[fl].pop(ra)
    files[fl][len(files[fl]) - 1] = files[fl][len(files[fl]) - 1].strip()

    # Cambia encabezado archivos
    for fl in files.keys():
        data = files[fl]
        data[0] = '% Template:     Template auxiliar LaTeX\n'
        data[10] = '% Sitio web del proyecto: [http://ppizarror.com/Template-Auxiliares/]\n'
        data[11] = '% Licencia MIT:           [https://opensource.org/licenses/MIT]\n'
        data[headerversionpos] = versionhead

    # Guarda los archivos
    for fl in files.keys():
        data = files[fl]
        newfl = open(subrlfolder + fl, 'w')
        for j in data:
            newfl.write(j)
        newfl.close()

    # Se obtiene la cantidad de líneas de código
    lc = 0
    for f in files.keys():
        lc += len(files[f])

    # Actualización a compacto
    fl = 'lib/initconf.tex'
    ra, _ = find_block(files[fl], 'Template.Version.Dev')
    files[fl][ra] = replace_argument(files[fl][ra], 1, versiondev + '-AUX-C')
    ra, _ = find_block(files[fl], 'Template.Tipo')
    files[fl][ra] = replace_argument(files[fl][ra], 1, 'Compacto')

    # Se crea ejemplo
    fl = open(subrlfolder + 'example.tex', 'w')
    data = files['lib/example.tex']
    for k in data:
        fl.write(k)
    fl.close()

    # Se crea compacto
    line = 0
    fl = open(subrlfolder + 'auxiliar.tex', 'w')
    data = files[mainfile]
    stconfig = False  # Indica si se han escrito comentarios en configuraciones

    for d in data:
        write = True
        if line < initdocumentline:
            fl.write(d)
            write = False
        # Si es una línea en blanco se agrega
        if d == '\n' and write:
            fl.write(d)
        else:
            # Si es un import pega el contenido
            # noinspection PyBroadException
            try:
                if d[0:6] == '\input':
                    libr = d.replace('\input{', '').replace('}', '').strip()
                    libr = libr.split(' ')[0]
                    if '.tex' not in libr:
                        libr += '.tex'
                    if libr != examplefile:

                        # Se escribe desde el largo del header en adelante
                        libdata = files[libr]  # Datos del import
                        libstirp = filestrip[libr]  # Eliminar espacios en blanco
                        libdelcom = filedelcoments[libr]  # Borrar comentarios

                        for libdatapos in range(headersize, len(libdata)):
                            srclin = libdata[libdatapos]

                            # Se borran los comentarios
                            if deletecoments and libdelcom:
                                if '%' in srclin:
                                    if libr == configfile:
                                        if srclin.upper() == srclin:
                                            if stconfig:
                                                fl.write('\n')
                                            fl.write(srclin)
                                            stconfig = True
                                            continue
                                    comments = srclin.strip().split('%')
                                    if comments[0] is '':
                                        srclin = ''
                                    else:
                                        srclin = srclin.replace('%' + comments[1], '')
                                        if libdatapos != len(libdata) - 1:
                                            srclin = srclin.strip() + '\n'
                                        else:
                                            srclin = srclin.strip()
                                elif srclin.strip() is '':
                                    srclin = ''
                            else:
                                if libr == configfile:
                                    # noinspection PyBroadException
                                    try:
                                        if libdata[libdatapos + 1][0] == '%' and srclin.strip() is '':
                                            srclin = ''
                                    except:
                                        pass

                            # Se ecribe la línea
                            if srclin is not '':
                                # Se aplica strip dependiendo del archivo
                                if libstirp:
                                    fl.write(srclin.strip())
                                else:
                                    fl.write(srclin)

                        fl.write('\n')  # Se agrega espacio vacío
                    else:
                        fl.write(d.replace('lib/', ''))
                    write = False
            except:
                pass

            # Se agrega un espacio en blanco a la página después del comentario
            if line >= initdocumentline and write:
                if d[0:2] == '% ' and d[3] != ' ' and d != '% CONFIGURACIONES\n':
                    if d != '% FIN DEL DOCUMENTO\n' and addwhitespace:
                        fl.write('\n')
                    d = d.replace('IMPORTACIÓN', 'DECLARACIÓN')
                    fl.write(d)
                elif d == '% CONFIGURACIONES\n':
                    pass
                else:
                    fl.write(d)

        # Aumenta la línea
        line += 1

    printfun(MSG_FOKTIMER.format((time.time() - t)))
    fl.close()

    # Compila el archivo
    if docompile and dosave:
        t = time.time()
        with open(os.devnull, 'w') as FNULL:
            printfun(MSG_DCOMPILE, end='')
            with Cd(subrlfolder):
                call(['pdflatex', 'auxiliar.tex'], stdout=FNULL, creationflags=CREATE_NO_WINDOW)
                t1 = time.time() - t
                call(['pdflatex', 'auxiliar.tex'], stdout=FNULL, creationflags=CREATE_NO_WINDOW)
                t2 = time.time() - t
                tmean = (t1 + t2) / 2
                printfun(MSG_FOKTIMER.format(tmean))

        # Se agregan las estadísticas
        add_stat(stat['FILE'], versiondev, tmean, dia, lc, versionhash)

        # Se plotean las estadísticas
        if plotstats:
            plot_stats(stat['FILE'], stat['CTIME'], stat['LCODE'])

    # Se exporta el proyecto normal
    czip = release['ZIP']['NORMAL']
    export_normal = Zip(czip['FILE'])
    export_normal.set_ghostpath(czip['GHOST'])
    export_normal.add_excepted_file(czip['EXCEPTED'])
    export_normal.add_file(czip['ADD']['FILES'])
    export_normal.add_folder(czip['ADD']['FOLDER'])
    export_normal.save()

    # Se exporta el proyecto único
    czip = release['ZIP']['COMPACT']
    export_single = Zip(czip['FILE'])
    export_single.set_ghostpath(czip['GHOST'])
    export_single.add_file(subrlfolder + 'auxiliar.tex')
    export_single.add_folder(subrlfolder + 'images')
    export_single.add_file(subrlfolder + 'lib/example.tex', subrlfolder + 'lib/')
    export_single.save()

    # Limpia el diccionario
    clear_dict(RELEASES['_INFORME'], 'FILES')
    clear_dict(RELEASES['AUXILIAR'], 'FILES')

    return