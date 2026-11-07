# all in one file

import os
import sys
import time
import traceback
import tempfile
import threading
import multiprocessing as mp
import uuid
import logging

from pdf2docx import Converter
from docx import Document

if __name__=="__main__":
    # 仅在GUI进程中使用 PyQt5
    import base64
    import lzma
    from PyQt5.QtCore import (
        Qt, QThread, QTimer, QObject, QSize, 
        QByteArray, QRectF, 
        pyqtSignal, pyqtSlot
    )
    from PyQt5.QtGui import (
        QIcon, QColor, QBrush, QFontDatabase, 
        QIconEngine, QPainter, QPixmap, QPalette
    )
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QStackedWidget, QToolButton, QButtonGroup, QLabel, QLineEdit,
        QListWidget, QListWidgetItem, QFileDialog, QFormLayout,
        QPushButton, QPlainTextEdit, QDialog, QMenu, QAbstractItemView,
        QMessageBox, QFrame, QSizePolicy, 
        QStyledItemDelegate, QStyleOptionViewItem
    )
    from PyQt5.QtSvg import QSvgRenderer

    STRINGS = {
        "pending": "排队中",
        "running": "运行中",
        "success": "成功",
        "failed": "失败",
        "stopped": "已停止",
        "submitting": "提交中", 
        "copy_log": "复制日志",
        "refresh_log": "刷新日志",
        "on_log_error": "获取日志失败: {}",
        "on_stop_task_error": "停止任务失败(id={}): {}",
        "on_poll_tasks_error": "轮询失败: {}",
        "settings": "转换设置",
        "file_list": "文件列表",
        "output_dir_placeholder": "留空则使用源文件目录",
        "browse_output_dir": "选择输出目录",
        "output_dir_label": "输出目录：",
        "pdf_password_placeholder": "留空表示无密码",
        "pdf_password_label": "PDF文档密码：",
        "drop_files_hint": "将PDF文件或文件夹拖入此处",
        "no_new_files_added": "未添加任何新PDF文件",
        "submit_failed": "提交失败: {}",
        "stop_failed": "停止失败: {}",
        "view_log": "查看日志",
        "stop_task": "停止任务",
        "remove_selected": "移除选中",
        "clear_finished": "清空已完成",
        "part_from_file": "文件: {}",
        "part_from_status": "状态: {}",
    }

    PRINT_ERROR = False  # 是否在控制台打印所有错误信息
    ICON_FILES = {
        "settings": "settings.svg",
        "file_list": "list_ul.svg",
        "folder": "folder.svg",
        "description": "console.svg",
        "stop": "stop.svg",
        "delete": "trash.svg",
        "clear_all": "eraser.svg",
        "copy": "copy.svg",
        "refresh": "refresh.svg",
        "help": "help.svg",
        "convert": "convert.svg",
    }
    STATUS_TEXT = {
        "pending": STRINGS["pending"],
        "running": STRINGS["running"],
        "success": STRINGS["success"],
        "failed": STRINGS["failed"],
        "stopped": STRINGS["stopped"],
        "submitting": STRINGS["submitting"],
    }

    STATUS_COLOR = {
        "pending": QColor("#666666"),
        "running": QColor("#1e88e5"),
        "success": QColor("#2e7d32"),
        "failed": QColor("#c62828"),
        "stopped": QColor("#e65100"),
        "submitting": QColor("#888888"),
    }
    END_STATUS = {"success", "failed", "stopped"}
    RAW_SVG_DATA = 'rAT%)=o\\O*k16n/!WXAE(\'"=7F>)aNi&>?^Ea8Z.M9\'<d"n1f*\'K@LDkkE.U,L5kXb_6\\rH@48=fd)3Ba"+XhF)U.u8=&JjDZ<ejdd/-kW_72K?S\'iOO*KW2\'dBQ1GJAs00Xg(]%\'<@qVrkP][.fL"IQGgjAGT-*VK"BN)-]2;XVDk^E8uL<P@DYr1b/.RPmVF0@4\'R>r[FG`o95E[s&ZJEgiZJW+iBpAX\\&t(faZ\\$)#$U/_k\\gHc\\!gCMIU>D#1m>TDf>Db]qG%;W"bMU]#-p^#7JfL`QWn!LA(cp=j4L&hol&K\'h]AoqThC+@BP0V@TI,271Yek@$.nhrY6]p>9M&a^.5*h!9F_cJP5N3^/NAHD1SCUUbk,X=e/AWR@02HeH8h7MrUh"5[&:?jIi3FnO6GgA?nPu/i.F#J"SB2YjpXlneN4dD0sa]q7C=QEEuk[Er;a%5)%gFHQOllG@Oq-,_)Z-&9bLe:!q^KhK]?61^*&J*+LU??E]-pJI?+3J!#Ha3&9W8QA_KbM:aVE=?E&2%3OUQjs3QC6g5BSk(;XtF6Gj]bm)<toc3YZ*,4)q8(D[jX:BAQ9.<7&="p\\K0n^i(\\\')qm_1?\\hSJ$T\\YoIaA+"+8kCqG?5_cJ>F4`@>/V&WI8e>SXm2PGQNELFGcU:k[n-ZM:g18A\\k<I/nO;FPQH9F,>CL$G,KQp[.VPb/MoS(9YW3G8b:rI5SdYEJFY*f=TSePjLgi$%k\\j9bE0`Q7o\\"F`Y0Nr8[GK"8<2bt;DR03jB/BkO\'1/r+j^S=TTGlj?j@9q??t3jKm[hj[EnX>TVIhlXi/fWjC_#V)J\'j6F0Z4[=-"0]3hGDdNPR+XG2*M"_k3l&0Ot/V,6Kr+C]po_&FkW^DbXquC4Pn_1$&Qgb@U(!ZfgqIq;-:k"2FX0t\\`KUdV-3lTfrKD9^\'?gVRm%G!QlpZeC`fS0i?CZUf=hOA2l2)2P.,5/D4Fd.JQ(jD-V#X>bNpZLP*OTc$P]9jH@cKPBW>\'(uT\\`1:P>N6_!C\'XTg(sdAn4_VD5S11?DgY:u=L4RMBE6E3D6o]r]jSW6t0)`%,-\']lYI;4F1IT?piPt0nl=Aur!LSp=?dtZ`U/nR5elu*.hX\'opC9o8(04e&N,0ict_L1XLZ6$l\'*?qq]rZ=Rspo0\\^AoEql:!=:Z(i0BG4rQU0uXb7?LZDQ)Fq+7W1)ti^n8lu:n_//+%0"K?rkU0D[Y_[oXlT->C9NMG!*3.OKH)H0ZSql"XS/tCkjs*-E$+FAI\'`Lq\\*f!NEV8u8\'o^B\\*oW$"\\kE+lR*se`HRb69O7pL=r7E3&\\Hq[uO"9q,$?T2>SU:bU+E"p2b84qDkbFVr,KltOhEO`lTD"1NZ">Q\'6,)#9^FHs8B%9"&)atp^],)7`pf!H[.5VC-/$W88G>r,8[:bfOP3BO-6B8bl(6+60R4muCU+45T10Dd0I[(tDd53%5<;GD6@l]-;cCsALu)+g-Qk:7C-O#\'f_r#U;9nV0V0EIfK=1)0TG9RBjRcGNLEBt?PGYtY_qC#[5JFngZhHkqA.H(0\'XP57RR,=lpQ@3KQ.TG+qW\'I7S[AAj4$[LBJ_4+\'6unCaX/=g#r0cUi4FiOS+`[A&GsWa:O9"KH!-mE[L7pDf;)fZ2N#q_Ih6!`(&AC@GA_Ab@hMJcD"/Uc<@J35HN8qiM24,\\q"J5!<40*C/=@b=$#RLN<1dKX\'Ap5f6E:ZPTT5l.i%+#B-L"-#7i\':RU]N(\'UXJ-7I%6idNAnS#@UOZ:l6q6<=cgQV/@:h=T?6m-n9!]DXCPh/J\\6`u"01HKd3O+r4TCdH1h.jt_(5!@2[1QIq*eDZGpp\'OKWNP\\sMuhC^Z>5Q0/K5]93Zqj>6haYLA\'QBXBkF1>9<8\'smX`D42mI)te@k_jUBB?P.4C#ujEHM`=9?DXYDNII.a9:a,h(C@K?GBD:4r<*m#Mg[LDe^=`>ge*aF\\/;>KgYc3gFTn)>7cma&S6M%E<h102XJ)\'?+Ien[I8,s2j+K-)iX\'YLZ$@[Oq\\:fd?oNo/#@$Y:6/u$)b-"M@KjUip^.s@tfu\\=>0^0j7)Koa`Z\\F00C5u1,6*irDJ8B1i!s68mSMlCY2F0h]Pgg)Y<FT3+&$=i&?<]VPb@EKP7:TZc.gX;K-FI4\'OfJA$phZCWEXD<>p.fm7fS.f!QgK8oDXIW(2\'!/KRFE$-.EfN!rC+UihVgOnd%s!TGAV3Hpf/KPbYH6A%!t=;F5IQ!:BW?7.Pb]57n$h4isoJKi^K<O7Tk);:Oq=Jdq<K-\'o*%pSe.._?q<NC)0GT;9&&uE<R+o[3l9AV"\'DbnGljm#$;Y%+e$<>n6@H;4<#^q2CFieZjI5IcaIr1J7W-%\\@+U8K/)PG6Lr\'\\Co/?T\'OqH]j^L;@k:oNJIijVf:2LNJZ!n_*fJq<d/7uU!9j`)+5lY2_>"#YgdDd72ToBCc@b.$4!<u;g)Pi:uPcDZQSUW_)F*/t(&2&Anhm-h?VJYdWB-#+;tHIV5p,HLDa^h]jAh-YTr%<P`N;A5TM"gI`>S?DBSL[&h=EDCHE\\7Tf1:6C_8TQh]pGPoJ-oBJ\'/<i)*(mjE^c]N%c#YZb69\\kU0Eql;Tq*$LmHDp4PmgJiRklPGGu/daIsk=#OVWSX`*=N/*\'\\W9",M[6oT[/ueVM.hqg_Vh?4r?lBl*a&mp\'49CGRnHGc/%W=bHKn1eiV["ak:M;#^a+;mNPG[n\\#R%UT"\\*kk.q:sO_8aMgJIUSSE44R0B*/6)u\\T[(d.?AZu3:p!b*N9"og)`?PeZ7)O^e-LU-Y?8-.S1?d1DlFq0(/?K;VP.C+kXjJp*!P[CGC)QaKKK,AY!:YL3UK\'dY[OST.^JFb00U/H(ZLd)mOf>*ut4HHOeL[/;BoG8lB(IFa[k42\'tE>o<9[1Nr>?WdgH?R\'#kmHb(QCF"ceZog)kEh_.`nue\\%8@7AedqCt@!6%@%/0^RO`.YZQGT1hqS`k_&N&6SN99idS7^SHldQqnl:%BM@jZ,"m(];2L]=3ft;+b=e2:@?V*WM+-o&5/HV:4oW_B<Rlm#=3iR:T2knf%K<DW\\XHA+/)r@uN\\s!TgR-\\P5BqBYK/I>CYK=)m4,\\f8b%F]qWrW6u=2S:9gi>`o)ScYt!YrH>;E`r=ioi&2Y.6_n^Ek*b5XfjKua5$mG$+4]l/u+Xj5_7V<iKW3+>rT*[gIDcjOg=I=(((iqtg/0QJ9*-*0*#06Luepn)hd`F9R6.W?SglY!CK`X[^:FHZ(MOL#oP<h0\'XeE(-=l[G$8r@p]CVsW=hW:*9.h5YW+JR*sI.6P<X3%V<WU%MU\\BQ\'sX%ZR9:TdYB0%_8]8),NHfKp8m/aUiGJTuhY2;=<.:`Zr^>$C<AB/`1C>QPETOWqI]_==qDZ0\\+b:-cs:*8`a#if8i"5#W_L9up%h^j3B&mbrR.c<h\'`7G=58a.@t\\D\'Cd-O[QYh1uHX-L*E>Q_3>B5-+@1:cN>9IgX%8G#dbS!<gB8crY1Ghp\'L4^^Eg)ZCLsl(j?kWH#^\'I,mP^"\'EsCZWXJZ\\9R<\\kLiI(G:j+LFL.R]\\keR2r@K8,*WES\'l^JA_F/cE.PTC#52h_JU&F?4kH48aCs25n?:U+5+CnH9!.Uc?#*\\(o?`HDdX@/qs6q+ag$lb$[k??nDOKf2D!91cf^S-YdM=!!<?/f0,nu*#b30G)O5ZDQXrEJlQ.q@bOWtch,cJ;Ou"HnFkB`4&<Y;o]7QTYLlskl[,tBK?kX%.rBm@r4mPU/7PUju!^_8<)EfJ?qB0^^^lR=+D6VBlNY7inpUYOAL\\]TnDWN0H(1`lBDg5f2QYri;cZE7$5A=G5AbDDtRX(86C>/1-a2!`Sq(\'6b"H[e6Gk(r`i%GN4JUT[dZ[<Arp<QG2>sCk[8u2p#\\VD>7VA\'cc=pjK7[[k%VCU2!eC9n&Fm63Ge3[]9#c-CL3MQ<?5-d2:cMQmc0pdU_[!o>R\\Q7X6k<%A8Ca[GJ^@qskWhm5[p%A-D;7pUQe/L!rr[g"eBGrKKjX%?=5DV#D9Gl\'j.[Ge(.W>-CBCfC@(OIAGLl8_D2nVR^*a9OeIr]q?_F9IAo<m94_m5u\\@6X-Ae5)1&@$!hYbkI<uKo&lu#\\Xi8kkm5RsOui/"5cNt8ruI]WILAY6mK[s>:KYmTJW9KocC/Yt=J#2S9_2ES[sZKAD*j<4o)k&2lb\'>B8!*h9)-nP%/[].6mWRq>ecGnr!r:>7;!U(i7W`_+3t-96Bo?R=D-aM?jt0$oD]AG#Lr;q3Vl`d3.\'k?49U\\RfF(=2lWaQ5K??`;2ns.H"]j\\pNG4"\'6N[!Oq#6KC;oA\\2lkoY6:Ys]\'RfVi8VOgXZ@lZ\'09&J#b*eEYc1S`q>I>H_X+&nLgMEHAXf-2[7G]apfeJ:];E@hj&K0Ak%5jmAHZUqHl<c!(<a!rL5>Ci(4?dkgt`%Ie.G+ttS!L,%TpLnA/Gk$V$EUCd8Za,;>Rmep718Y[B=PWIhDY@qsKdK%N&iKB"M`k3lD3#D1\')*OUs]Y\\N2K]ODrOFa"1QD`b!cF4\\GeMc)npbtu&;fb;1LO=:5&L%FghF30[P>a-7J*GCV"AdDbOfeF)Un/e6OZcBD)taZ\\guV5cX.V[XX3%A`Yq+\'>?sFthX77Y`No)M$EEH@dX\';HIXb&EX)D(uC^\'M3DOh*,tA&lVC;$_O_6gI*Zgj7W?O;V1\\:T&34JU7/moa4,)oYrh#r-,9EL#73<kidq7)l]<u\'(=Mk)3Y/\\/XA8&#3*R,7kS8(f]\'F$FB-]_]PcDpAI4bp<`.E/a5OLDVJfm!dt@1QOID#nC"JU.88m2jD-/g/dGk3r4^B!,!\\^"LZ0Je\'(\\nf1A0AJnrd-=DLN!&6$"B/*qO4eFAO9sJ@fTeAl>i#%=*)GD/r2).XlgB=Bqg^[_%LIfdJJ+ZW$(2,DJ,6%b[ho08BE!\\qo7db.UJ(AH$?c`OWhYm4\'mjoltmk(?WSR3&\'S[+P?MfZ$tC/-aXm\\Gb:.ND65ERhr8d;#)k0"g`C3<AG%*N6i04DqRnJ$uL@I--FZ>Q^U/!4;-b6kcO/VkA0=bn)LYDB"1<&SkB;\'0dcQgX6JuLdm88`sTN#G1hjR;+K/(Lm[U/Xb&:Etjm=o3U.Cb:AAVkamgVPog5^\\QrMI":!f[T9Eu7h$Bf$YO0_jZEEGYNXL"W4O(,&hW"[TE%uqPs]8G;;7VFZ>Z3>$"UlWeGop(qeG$66o0O,<.(23+op%&?Otfu\'iBaLb[`B?-@W6kD\\@rW"H;U3%qA>7ZO$`bo!B]U$PBa9;$n]KlEWb:^Db+3isobth-(@kn>K,.U_WpI*<rjD-;pMZq<hST@ib\\BmD`bR(\'mKg]cVF2k6Fo`@3(?u.mrnVa7rjT"s\'&DUWKHXmRDjRe\'mY]-P[AcerurEi0L*]kaMNSAZ;N"@"/GuR!E(Jm[R:0]iDRlfZ5]4\\i=q`\'\\RQ-:?h/P:d8[I4O>Lh;\\lF&2/G\'EdeG<Oj>9XBcdPm\\r6aT4\'3cN,J-cS2LH3k\\^moK0M1>HS_\\*h#j$YeO)hV=Q$\'#EYLJN%8[+5j\\m\\)mdIOgPHC2Kf7XM%.R!T,aB=7ol$Z@%<5LlPeJX=JR\\X$N20TQD@0(u](@C6k=O@K5>2]39]/F8u:@GE^P1cI7LQ!!/*)l>?S%f<YXLZ,C;P!WW3#!!HG.'
    svg_data = dict(eval(lzma.decompress(base64.a85decode(RAW_SVG_DATA)).decode('utf-8')))

    RAW_QSS_DATA = 'rAT%)=o\\O*k16n/!WXAE(\'"=7F>)aNi!Ct:[TrkJ#RfdP\']Z\\:!26=+dYa6\\0VMkN2\\\\-IB[p\'ti"h/>T(Wnep6,4&`HkbFmS:FG<bW+A6c7-M=GZ.n%[a5m15rM6N72<7I8](],HiS\'l>S+T76Y%>Ppj03aq[4%j9U$g?LIo^&Y0rB=GG19\\4Hc@<!npq=teV^6,,!:92[`6kJ=)8V^An-e=Q@.AW#C,7tpB$Va^pH"J[BuTj`d>JG,Y4gul-Q+VS;21%Bmpofthg6O#OEpoAsVa5SW1,P#;[,-MG?G%d=fV@gF+3j,]m4Q3W6J3;jbVA-!q\')2\'t_$]!dC<(T3_q55Mi(Q9k-n1(spWI$)OOfGSWSe1mMb2d.dNWZ!;%(V.]O)"k"-P!*>nE5cLo<G\\]UtF\\29$3N$PoUC!$SB]Q7Jb7eGr%(<&(Y\'lCmOhBC"FGR.RgbIsgK53S*pF>+8h.Ooi+3@>3+.n*C!<q%![&0gOs*1ZaK%MLhjMRe>9#QT`A9f&lgq!k5!V#aF6E=Zp41@$3LS-3\'qQnc(VT!ooEr$$3?6W$KAs(/^pojd8)*-Xh5&l%j)-?tOK%34_2)N0:^dMc(M.;3lID<3=d<jmB@o=/_&c(&pa,9adb)f%CgemQ/.+I[t)n9(([R4c<le)mroDKMq".dB`%,QuOKX8N\'/<YKa?;\\Vrah@>#%uO8T,NK7e7T4(\'X[Uhoed&mu!9T!J*HV<U\\":;iYfqUp=G?5Tf<0`\\mJ/qOV!oC6>gFuNbQH1,j*oLLMsOTPSUo;i&hSW.ALLQDd@eLd@pR(k\\`gq(>B!?;t&N4J[j7iQ4ZMHKPo,amtg1+,R87>2,)qlEp%81$Au$//0SW^/;QN]pnb@0UMOAM\'QF%O#s7K\'*Y$pMZ,4K,2rOli7"cWA0%o,1)"t!!1LOXqC^7U&S-TZ,C;P!WW3#!!HG.'
    QSS = lzma.decompress(base64.a85decode(RAW_QSS_DATA)).decode('utf-8')

    
def convert(src_path:str, dest_path:str=None, password=None):
    """
    Convert a PDF file to a DOCX file.

    :param src_path: The path to the source PDF file.
    :param dest_path: The path to the destination DOCX file.
    :param password: The password for the PDF file, if it is encrypted.
    """
    src_path = os.path.abspath(src_path)
    if not os.path.exists(src_path):
        raise FileNotFoundError(f"The source file '{src_path}' does not exist.")
    if not os.access(src_path, os.R_OK):
        raise PermissionError(f"The source file '{src_path}' is not readable.")

    if dest_path is None:
        dest_path = os.path.splitext(src_path)[0] + '.docx'
    if not dest_path.endswith('.docx'):
        dest_path += '.docx'
    dest_path = os.path.abspath(dest_path)
    if os.path.exists(dest_path):
        prefix, suffix = os.path.splitext(dest_path)
        appendix = 1
        final_dest_path = f"{prefix}_{appendix}{suffix}"
        while os.path.exists(final_dest_path):
            appendix += 1
            final_dest_path = f"{prefix}_{appendix}{suffix}"
        dest_path = final_dest_path
    
    if not os.access(os.path.dirname(dest_path), os.W_OK):
        raise PermissionError(f"The destination directory '{os.path.dirname(dest_path)}' is not writable.")
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = f"{temp_dir}/{os.path.basename(dest_path)}"
        cv = Converter(src_path, password=password)
        cv.convert(temp_file_path, start=0, end=None)
        cv.close()
        doc = Document(temp_file_path)
        props = doc.core_properties
        props.author=''
        props.comments=''
        doc.save(dest_path)


def _run_convert(convert_func, src_path, dest_path, password, conn):
    """子进程里的工作函数：捕获 stdout/stderr 写入 Pipe"""
    class PipeWriter:
        """A file-like object that writes to a multiprocessing connection."""
        __slots__ = ("_conn",)
        def __init__(self, conn):
            self._conn = conn
        def write(self, text):
            if text:
                self._conn.send(text)
        def flush(self):
            pass

    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout = PipeWriter(conn)
    sys.stderr = PipeWriter(conn)

    root = logging.getLogger()
    formatters = []
    for handler in root.handlers:
        formatters.append(handler.formatter)
        root.removeHandler(handler)
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(formatters[0] if formatters else logging.Formatter())
    root.addHandler(handler)

    try:
        convert_func(src_path, dest_path, password)
    except Exception:
        traceback.print_exc()   # 会写入 conn
        raise
    finally:
        sys.stdout = old_out
        sys.stderr = old_err
        conn.close()


class PDFConvertManager:
    def __init__(self, convert_func, max_concurrency=None):
        self._convert_func = convert_func
        self._max_concurrency = max_concurrency or os.cpu_count() or 2
        self._tasks = {}
        self._pending_queue = []
        self._running_count = 0
        self._lock = threading.RLock()

    # ---------- 提交任务 ----------
    def submit(self, src_path, dest_path=None, password=None) -> str:
        """
        提交转换任务

        :param src_path: 源 PDF 文件路径
        :param dest_path: 目标 DOCX 文件路径
        :param password: PDF 文件密码
        :return: 任务ID
        """
        # 生成任务的UUID
        task_id = uuid.uuid4().hex

        # 构造任务
        task = {
            "task_id": task_id,
            "src_path": src_path,
            "dest_path": dest_path,
            "password": password,
            "status": "pending",
            "process": None,
            "log_conn": None,
            "log_lines": [],
            "created_at": time.time(),
            "finished_at": None,
            "exitcode": None,
        }
        # 记录
        with self._lock:
            self._tasks[task_id] = task
            self._pending_queue.append(task_id)
        # 调度
        self._schedule()

        return task_id

    def _schedule(self):
        # 调度下一个任务
        # 警告：绝对不要在锁内调用该函数！！！
        with self._lock:
            # 限制并发
            if self._running_count >= self._max_concurrency:
                return
            # 没有待处理的任务
            if not self._pending_queue:
                return

            # 从队列取出一个 task
            task_id = self._pending_queue.pop(0)
            task = self._tasks.get(task_id)
            if task is None or task["status"] != "pending":
                return

            # 创建进程和管道
            parent_conn, child_conn = mp.Pipe(duplex=False)
            process = mp.Process(
                target=_run_convert,
                args=(self._convert_func,
                    task["src_path"], task["dest_path"], task["password"],
                    child_conn),
                daemon=True
            )
            task["process"] = process
            task["log_conn"] = parent_conn
            task["status"] = "running"
            self._running_count += 1

            process.start()

            # 启动日志读取线程
            threading.Thread(target=self._reader,
                            args=(task_id,), daemon=True).start()


    # ---------- 读取日志并更新状态 ----------
    def _reader(self, task_id):
        # 获取完整的task对象，获取管道
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return
            conn = task["log_conn"]

        try:
            # 主循环：读取管道中的日志信息
            while True:
                try:
                    # 读取一行日志，如果管道关闭则退出循环（阻塞）
                    line = conn.recv()
                except EOFError:
                    break
                # 写入日志列表
                with self._lock:
                    if task_id in self._tasks:
                        self._tasks[task_id]["log_lines"].append(line)
                    else:
                        # 任务已被删除，退出循环
                        break
        finally:
            # 管道关闭 = 子进程结束，更新任务状态
            with self._lock:
                task = self._tasks.get(task_id)
                # 如果任务仍然存在且状态为 running，则更新状态为 success/failed/stopped
                if task is not None and task["status"] == "running":
                    task["process"].join()
                    task["finished_at"] = time.time()
                    self._running_count -= 1
                    task["exitcode"] = task["process"].exitcode
                    if task["exitcode"] == 0:
                        task["status"] = "success"
                    elif task["exitcode"] is not None and task["exitcode"] < 0:
                        task["status"] = "stopped"
                    else:
                        task["status"] = "failed"
                # 否则直接不管
            # 然后关闭管道
            conn.close()
            # 尝试调度下一个任务
            self._schedule()
        return

    # ---------- 查询 ----------
    def get_task(self, task_id, throw=True) -> dict:
        """
        获取任务信息

        :param task_id: 任务ID
        :param throw: 如果任务不存在，是否抛出 KeyError
        :return: 任务信息字典
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                if throw:
                    raise KeyError(task_id)
                else:
                    return None
            return {
                "task_id": task["task_id"],
                "src_path": task["src_path"],
                "dest_path": task["dest_path"],
                "status": task["status"],
                "created_at": task["created_at"],
                "finished_at": task["finished_at"],
                "exitcode": task["exitcode"],
                "log": "".join(task["log_lines"]),
            }

    def get_tasks(self) -> list:
        """
        获取所有任务信息

        :return: 任务信息列表
        """
        with self._lock:
            return [
                {
                    "task_id": t["task_id"],
                    "src_path": t["src_path"],
                    "dest_path": t["dest_path"],
                    "status": t["status"],
                    "created_at": t["created_at"],
                    "finished_at": t["finished_at"],
                    "exitcode": t["exitcode"],
                }
                for t in self._tasks.values()
            ]

    def get_log(self, task_id) -> str:
        """
        获取任务日志

        :param task_id: 任务ID
        :return: 任务日志字符串
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                raise KeyError(task_id)
            return "".join(task["log_lines"])

    # ---------- 停止 / 删除 ----------
    def _stop_process(self, process, timeout=3):
        """强制终止一个进程：先终止，再等待，必要时强杀。"""
        if not process.is_alive():
            return
        process.terminate()
        process.join(timeout=timeout)
        if process.is_alive():
            process.kill()
            process.join(timeout=timeout)

    def stop(self, task_id) -> bool:
        """
        停止一个正在运行的任务

        :param task_id: 任务ID
        :return: True表示成功停止，False表示任务不存在或已结束
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None or task["status"] != "running":
                return False
            process = task["process"]

        # 在锁外终止进程，避免阻塞其他线程
        self._stop_process(process)
        finished_at = time.time()

        with self._lock:
            task = self._tasks.get(task_id)
            if task is not None and task["status"] == "running":
                task["status"] = "stopped"
                task["finished_at"] = finished_at
                task["exitcode"] = process.exitcode
                self._running_count -= 1
        # 在锁外尝试调度下一个任务
        self._schedule()

        return True

    def delete(self, task_id):
        """
        删除一个任务（无论是否运行中），会尝试终止进程并清理资源。

        :param task_id: 任务ID
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                raise KeyError(task_id)
            process = task["process"]
            was_running = task["status"] == "running"
            self._tasks.pop(task_id) # 阻止其它线程访问这个任务
            log_conn = task["log_conn"]

        # 锁外终止进程（如果在运行）
        if was_running:
            self._stop_process(process)
            with self._lock:
                self._running_count -= 1
            self._schedule()
        # 关闭管道连接等资源
        log_conn.close()



if __name__ == "__main__":
    # 主进程中的GUI部分
    class SvgIconEngine(QIconEngine):
        """从字节串/字符串创建矢量 QIcon 的核心引擎"""

        def __init__(self, svg_data):
            super().__init__()
            if isinstance(svg_data, str):
                svg_data = svg_data.encode('utf-8')
            self.svg_bytes = QByteArray(svg_data)
            self.renderer = QSvgRenderer(self.svg_bytes)

        def paint(self, painter, rect, mode, state):
            """核心绘制方法：把 SVG 渲染到给定矩形区域"""
            self.renderer.render(painter, rect)

        def pixmap(self, size, mode, state):
            """生成指定尺寸的 QPixmap（有些场景如 QListView 会调用）"""
            pixmap = QPixmap(size)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            self.renderer.render(painter, QRectF(0, 0, size.width(), size.height()))
            painter.end()
            return pixmap

        def clone(self):
            """必须实现，保证 QIcon 复制时引擎也被正确复制"""
            return SvgIconEngine(bytes(self.svg_bytes))

    class SvgIconManager(dict):
        def __init__(self, svg_data):
            super().__init__()
            for name, svg_content in svg_data.items():
                self[name] = QIcon(SvgIconEngine(svg_content))

    # 一个普通的支持拖放的 QWidget，用于接收文件或文件夹拖放
    class DropWidget(QWidget):
        files_dropped = pyqtSignal(list)

        def dragEnterEvent(self, event):
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
            else:
                event.ignore()

        def dragMoveEvent(self, event):
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
            else:
                event.ignore()

        def dropEvent(self, event):
            paths = [
                url.toLocalFile()
                for url in event.mimeData().urls()
                if url.isLocalFile()
            ]
            if paths:
                self.files_dropped.emit(paths)
            event.acceptProposedAction()


    # 为了在选中状态下区分颜色，需要自定义绘制
    class StatusColorDelegate(QStyledItemDelegate):
        def paint(self, painter, option, index):
            fg = index.data(Qt.ForegroundRole)
            if fg is not None:
                # 复制一份 option，避免修改影响其他绘制
                opt = QStyleOptionViewItem(option)
                palette = opt.palette
                # 同时覆盖普通文字和高亮文字颜色
                palette.setBrush(QPalette.Text, fg)
                palette.setBrush(QPalette.HighlightedText, fg)
                opt.palette = palette
                option = opt
            super().paint(painter, option, index)

    class FileListWidget(QListWidget):
        files_dropped = pyqtSignal(list)

        def __init__(self, parent=None):
            super().__init__(parent)
            self.setAcceptDrops(True)
            self.setItemDelegate(StatusColorDelegate(self))
            self.setDragDropMode(QAbstractItemView.DropOnly)
            self._empty_hint = None

        def set_empty_hint(self, hint: QLabel):
            self._empty_hint = hint
            hint.setParent(self.viewport())
            hint.setAttribute(Qt.WA_TransparentForMouseEvents)
            self._layout_hint()

        def resizeEvent(self, event):
            super().resizeEvent(event)
            self._layout_hint()

        def _layout_hint(self):
            if self._empty_hint is not None:
                self._empty_hint.setGeometry(
                    0, 0, self.viewport().width(), self.viewport().height()
                )

        def dragEnterEvent(self, event):
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
            else:
                event.ignore()

        def dragMoveEvent(self, event):
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
            else:
                event.ignore()

        def dropEvent(self, event):
            paths = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    paths.append(url.toLocalFile())
            if paths:
                self.files_dropped.emit(paths)
            event.acceptProposedAction()


    class LogDialog(QDialog):
        refresh_requested = pyqtSignal(str)

        def __init__(self, task_id, icons=None, parent=None):
            super().__init__(parent)
            self._task_id = task_id
            self._icons = icons or {}
            self.setWindowTitle(f"日志 - {task_id}")
            self.resize(600, 400)

            self._log_edit = QPlainTextEdit()
            self._log_edit.setReadOnly(True)
            self._log_edit.setLineWrapMode(QPlainTextEdit.NoWrap)
            self._log_edit.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))

            copy_btn = QPushButton()
            if "copy" in self._icons:
                copy_btn.setIcon(self._icons["copy"])
            copy_btn.setToolTip(STRINGS["copy_log"])
            copy_btn.clicked.connect(self._copy_log)

            refresh_btn = QPushButton()
            if "refresh" in self._icons:
                refresh_btn.setIcon(self._icons["refresh"])
            refresh_btn.setToolTip(STRINGS["refresh_log"])
            refresh_btn.clicked.connect(
                lambda: self.refresh_requested.emit(self._task_id)
            )

            btn_layout = QHBoxLayout()
            btn_layout.addStretch(1)
            btn_layout.addWidget(copy_btn)
            btn_layout.addWidget(refresh_btn)

            layout = QVBoxLayout()
            layout.addWidget(self._log_edit)
            layout.addLayout(btn_layout)
            self.setLayout(layout)

            self._refresh_timer = QTimer(self)
            self._refresh_timer.setInterval(500)
            self._refresh_timer.timeout.connect(self._auto_refresh)
            self._refresh_timer.start()

        def on_log_ready(self, task_id, log):
            if task_id == self._task_id:
                self._log_edit.setPlainText(log)
                scrollbar = self._log_edit.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())

        def on_log_error(self, task_id, error):
            if task_id == self._task_id:
                self._log_edit.setPlainText(STRINGS["on_log_error"].format(error))
                scrollbar = self._log_edit.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())

        def _copy_log(self):
            self._log_edit.copy()

        def _auto_refresh(self):
            if self._task_status in ("pending", "running", "submitting"):
                self.refresh_requested.emit(self._task_id)
            else:
                self._refresh_timer.stop()
        
        def update_task_status(self, status):
            self._task_status = status
            if status in ("success", "failed", "stopped") and self._refresh_timer.isActive():
                self.refresh_requested.emit(self._task_id)
                self._refresh_timer.stop()


    class Worker(QObject):
        tasks_updated = pyqtSignal(list)
        task_submitted = pyqtSignal(str, str)
        task_submit_failed = pyqtSignal(str, str)
        task_stopped = pyqtSignal(str, bool)
        log_ready = pyqtSignal(str, str)
        log_error = pyqtSignal(str, str)
        worker_error = pyqtSignal(str)

        def __init__(self, manager, parent=None):
            super().__init__(parent)
            self._manager = manager
            self._timer = None

        @pyqtSlot()
        def start(self):
            self._timer = QTimer(self)
            self._timer.setInterval(500)
            self._timer.timeout.connect(self._poll_tasks)
            self._timer.start()

        @pyqtSlot(list)
        def submit_tasks(self, tasks):
            for task in tasks:
                try:
                    task_id = self._manager.submit(
                        task["src_path"],
                        task.get("dest_path"),
                        task.get("password")
                    )
                    self.task_submitted.emit(task_id, task["src_path"])
                except Exception as e:
                    if PRINT_ERROR: traceback.print_exc()
                    self.task_submit_failed.emit(task["src_path"], str(e))

        @pyqtSlot(str)
        def stop_task(self, task_id):
            try:
                ok = self._manager.stop(task_id)
                self.task_stopped.emit(task_id, bool(ok))
            except Exception as e:
                if PRINT_ERROR: traceback.print_exc()
                self.worker_error.emit(STRINGS["on_stop_task_error"].format(task_id, str(e)))

        @pyqtSlot(str)
        def get_log(self, task_id):
            try:
                log = self._manager.get_log(task_id)
                self.log_ready.emit(task_id, log)
            except Exception as e:
                if PRINT_ERROR: traceback.print_exc()
                self.log_error.emit(task_id, str(e))

        @pyqtSlot()
        def shutdown(self):
            if self._timer is not None:
                self._timer.stop()
                self._timer.deleteLater()
                self._timer = None
            self.thread().quit()

        def _poll_tasks(self):
            try:
                tasks = self._manager.get_tasks()
                self.tasks_updated.emit(tasks)
            except Exception as e:
                if PRINT_ERROR: traceback.print_exc()
                self.worker_error.emit(STRINGS["on_poll_tasks_error"].format(str(e)))


    class MainWindow(QMainWindow):
        request_submit_tasks = pyqtSignal(list)
        request_stop_task = pyqtSignal(str)
        request_get_log = pyqtSignal(str)
        request_shutdown = pyqtSignal()

        def __init__(self):
            super().__init__()
            self.setStyleSheet(QSS)
            self.setWindowTitle("PDF To Word")
            self.resize(800, 500)

            self._icons = self._load_icons()
            self.setWindowIcon(self._icons["convert"])

            self._added_paths = set()          # normalized absolute path -> None
            self._src_path_to_row = {}         # normalized absolute path -> row
            self._task_id_to_row = {}          # task_id -> row
            self._log_dialog = None

            self._build_ui()
            self._create_worker_thread()
            self.show()

        # ---------- icons ----------
        def _load_icons(self):
            svg_data_mapped = {name:svg_data[filename] for name, filename in ICON_FILES.items()}
            return SvgIconManager(svg_data_mapped)

        # ---------- UI ----------
        def _build_ui(self):
            central = QWidget()
            self.setCentralWidget(central)
            root_layout = QHBoxLayout(central)
            root_layout.setContentsMargins(0, 0, 0, 0)
            root_layout.setSpacing(0)

            # 左侧导航
            nav = QWidget()
            nav.setFixedWidth(80)
            nav_layout = QVBoxLayout(nav)
            nav_layout.setContentsMargins(0, 0, 0, 0)
            nav_layout.setSpacing(0)
            nav_layout.setAlignment(Qt.AlignTop)

            self.settings_btn = QToolButton()
            self.settings_btn.setIcon(self._icons["settings"])
            self.settings_btn.setIconSize(QSize(40, 40))
            self.settings_btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
            self.settings_btn.setCheckable(True)
            self.settings_btn.setToolTip(STRINGS["settings"])
            self.settings_btn.setAutoRaise(True)
            self.settings_btn.setObjectName("navButton")

            self.files_btn = QToolButton()
            self.files_btn.setIcon(self._icons["file_list"])
            self.files_btn.setIconSize(QSize(40, 40))
            self.files_btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
            self.files_btn.setCheckable(True)
            self.files_btn.setChecked(True)
            self.files_btn.setToolTip(STRINGS["file_list"])
            self.files_btn.setAutoRaise(True)
            self.files_btn.setObjectName("navButton")

            self._nav_group = QButtonGroup(self)
            self._nav_group.setExclusive(True)
            self._nav_group.addButton(self.files_btn, 0)
            self._nav_group.addButton(self.settings_btn, 1)
            self._nav_group.buttonClicked.connect(self._on_nav_clicked)

            nav_layout.addWidget(self.files_btn)
            nav_layout.addWidget(self.settings_btn)

            # 右侧页面
            self.stack = QStackedWidget()
            self.stack.addWidget(self._create_files_page())
            self.stack.addWidget(self._create_settings_page())

            root_layout.addWidget(nav)
            root_layout.addWidget(self.stack, 1)

        def _create_settings_page(self):
            page = QWidget()
            outer = QHBoxLayout(page)
            outer.setContentsMargins(20, 20, 20, 20)

            card = QFrame()
            card.setObjectName("card")
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(24, 24, 24, 24)
            card_layout.setSpacing(16)

            form = QFormLayout()
            form.setVerticalSpacing(16)
            form.setLabelAlignment(Qt.AlignRight)

            self.output_dir_edit = QLineEdit()
            self.output_dir_edit.setPlaceholderText(STRINGS["output_dir_placeholder"])

            browse_btn = QToolButton()
            browse_btn.setIcon(self._icons["folder"])
            browse_btn.setToolTip(STRINGS["browse_output_dir"])
            browse_btn.clicked.connect(self._browse_output_dir)

            dir_layout = QHBoxLayout()
            dir_layout.addWidget(self.output_dir_edit)
            dir_layout.addWidget(browse_btn)
            form.addRow(STRINGS["output_dir_label"], dir_layout)

            self.password_edit = QLineEdit()
            self.password_edit.setEchoMode(QLineEdit.Password)
            self.password_edit.setPlaceholderText(STRINGS["pdf_password_placeholder"])
            form.addRow(STRINGS["pdf_password_label"], self.password_edit)

            card_layout.addLayout(form)
            outer.addWidget(card, 1)   # 占满剩余宽度
            return page


        def _create_files_page(self):
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(20, 20, 20, 20)

            self.list_widget = FileListWidget()
            self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
            self.list_widget.customContextMenuRequested.connect(
                self._show_context_menu
            )
            self.list_widget.files_dropped.connect(self._on_files_dropped)

            self._empty_hint = QLabel(STRINGS["drop_files_hint"])
            self._empty_hint.setAlignment(Qt.AlignCenter)
            self._empty_hint.setStyleSheet("color: #888888;")
            self._empty_hint.setAttribute(Qt.WA_TransparentForMouseEvents)
            self.list_widget.set_empty_hint(self._empty_hint)

            layout.addWidget(self.list_widget)
            return page

        def _browse_output_dir(self):
            directory = QFileDialog.getExistingDirectory(self, STRINGS["browse_output_dir"])
            if directory:
                self.output_dir_edit.setText(directory)

        def _on_nav_clicked(self, button):
            self.stack.setCurrentIndex(self._nav_group.id(button))

        # ---------- Worker 线程 ----------
        def _create_worker_thread(self):
            manager = PDFConvertManager(convert)
            self._worker = Worker(manager)
            self._thread = QThread(self)
            self._worker.moveToThread(self._thread)

            # 主线程 -> Worker（QueuedConnection 显式指定）
            self.request_submit_tasks.connect(
                self._worker.submit_tasks, Qt.QueuedConnection
            )
            self.request_stop_task.connect(
                self._worker.stop_task, Qt.QueuedConnection
            )
            self.request_get_log.connect(
                self._worker.get_log, Qt.QueuedConnection
            )
            self.request_shutdown.connect(
                self._worker.shutdown, Qt.QueuedConnection
            )

            # Worker -> 主线程（QueuedConnection 显式指定）
            self._worker.tasks_updated.connect(
                self._on_tasks_updated, Qt.QueuedConnection
            )
            self._worker.task_submitted.connect(
                self._on_task_submitted, Qt.QueuedConnection
            )
            self._worker.task_submit_failed.connect(
                self._on_task_submit_failed, Qt.QueuedConnection
            )
            self._worker.task_stopped.connect(
                self._on_task_stopped, Qt.QueuedConnection
            )
            self._worker.worker_error.connect(
                self._on_worker_error, Qt.QueuedConnection
            )

            self._thread.started.connect(self._worker.start)
            self._thread.start()

        # ---------- 文件添加与提交 ----------
        def _on_files_dropped(self, paths):
            new_files = []
            for p in paths:
                if os.path.isdir(p):
                    for root, _dirs, files in os.walk(p):
                        for name in files:
                            if name.lower().endswith(".pdf"):
                                new_files.append(os.path.join(root, name))
                elif os.path.isfile(p) and p.lower().endswith(".pdf"):
                    new_files.append(p)

            added_any = False
            for path in new_files:
                norm = os.path.normcase(os.path.abspath(path))
                if norm in self._added_paths:
                    continue
                self._added_paths.add(norm)
                self._add_item(norm, os.path.abspath(path))
                added_any = True

            if not added_any:
                self.statusBar().showMessage(STRINGS["no_new_files_added"], 3000)

        def _add_item(self, norm, src_path):
            item = QListWidgetItem()
            data = {
                "norm": norm,
                "src": src_path,
                "task_id": None,
                "status": "submitting",
            }
            item.setData(Qt.UserRole, data)
            self.list_widget.addItem(item)
            row = self.list_widget.row(item)
            self._src_path_to_row[norm] = row
            self._refresh_item(item)
            self._update_empty_hint()

            dest_path = self._build_dest_path(src_path)
            password = self._get_password()
            self.request_submit_tasks.emit([
                {"src_path": src_path, "dest_path": dest_path, "password": password}
            ])

        def _build_dest_path(self, src_path):
            stem = os.path.splitext(os.path.basename(src_path))[0]
            output_dir = self.output_dir_edit.text().strip()
            if output_dir:
                return os.path.join(output_dir, stem + ".docx")
            return os.path.join(os.path.dirname(src_path), stem + ".docx")

        def _get_password(self):
            pwd = self.password_edit.text().strip()
            return pwd if pwd else None

        # ---------- Worker 信号处理 ----------
        def _on_tasks_updated(self, tasks):
            for task in tasks:
                tid = task.get("task_id")
                if not tid or tid not in self._task_id_to_row:
                    continue
                row = self._task_id_to_row[tid]
                item = self.list_widget.item(row)
                if item is None:
                    continue
                data = item.data(Qt.UserRole)
                if data is None:
                    continue
                data["status"] = task.get("status", data.get("status", "unknown"))
                if task.get("exitcode") is not None:
                    data["exitcode"] = task["exitcode"]
                else:
                    data.pop("exitcode", None)
                item.setData(Qt.UserRole, data)
                self._refresh_item(item)

                if self._log_dialog is not None and self._log_dialog._task_id == tid:
                    self._log_dialog.update_task_status(task.get("status", ""))

        def _on_task_submitted(self, task_id, src_path):
            norm = os.path.normcase(os.path.abspath(src_path))
            row = self._src_path_to_row.get(norm)
            if row is None:
                return
            item = self.list_widget.item(row)
            if item is None:
                return
            data = item.data(Qt.UserRole)
            data["task_id"] = task_id
            data["status"] = "pending"
            item.setData(Qt.UserRole, data)
            self._task_id_to_row[task_id] = row
            self._refresh_item(item)

        def _on_task_submit_failed(self, src_path, error):
            norm = os.path.normcase(os.path.abspath(src_path))
            row = self._src_path_to_row.get(norm)
            if row is None:
                return
            item = self.list_widget.item(row)
            if item is None:
                return
            data = item.data(Qt.UserRole)
            data["status"] = "failed"
            item.setData(Qt.UserRole, data)
            self._refresh_item(item)
            self.statusBar().showMessage(STRINGS["submit_failed"].format(error), 3000)

        def _on_task_stopped(self, task_id, success):
            if not success:
                self.statusBar().showMessage(STRINGS["stop_failed"].format(task_id), 3000)
            # 成功时状态由轮询更新

        def _on_worker_error(self, message):
            self.statusBar().showMessage(message, 5000)

        # ---------- UI 辅助 ----------
        def _refresh_item(self, item):
            data = item.data(Qt.UserRole)
            if not data:
                return
            src = data["src"]
            status = data.get("status", "unknown")
            status_text = STATUS_TEXT.get(status, status)
            item.setText(f"{os.path.basename(src)} — {status_text}")
            item.setForeground(QBrush(STATUS_COLOR.get(status, QColor("#000000"))))

            parts = [STRINGS["part_from_file"].format(src), STRINGS["part_from_status"].format(status_text)]
            tid = data.get("task_id")
            if tid:
                parts.append(f"task_id: {tid}")
            if data.get("exitcode") is not None:
                parts.append(f"exitcode: {data['exitcode']}")
            item.setToolTip("\n".join(parts))

        def _update_empty_hint(self):
            self._empty_hint.setVisible(self.list_widget.count() == 0)

        # ---------- 右键菜单 ----------
        def _show_context_menu(self, pos):
            item = self.list_widget.itemAt(pos)
            if item is None:
                return

            menu = QMenu(self)
            act_log = menu.addAction(self._icons["description"], STRINGS["view_log"])
            act_stop = menu.addAction(self._icons["stop"], STRINGS["stop_task"])
            menu.addSeparator()
            act_remove = menu.addAction(self._icons["delete"], STRINGS["remove_selected"])
            act_clear = menu.addAction(self._icons["clear_all"], STRINGS["clear_finished"])

            chosen = menu.exec_(self.list_widget.mapToGlobal(pos))
            if chosen == act_log:
                self._show_log()
            elif chosen == act_stop:
                self._stop_selected()
            elif chosen == act_remove:
                self._remove_selected()
            elif chosen == act_clear:
                self._clear_finished()

        def _show_log(self):
            for item in self.list_widget.selectedItems():
                data = item.data(Qt.UserRole)
                tid = data.get("task_id")
                if tid:
                    self._open_log_dialog(tid)
                    return

        def _stop_selected(self):
            for item in self.list_widget.selectedItems():
                data = item.data(Qt.UserRole)
                tid = data.get("task_id")
                status = data.get("status")
                if tid and status in ("pending", "running"):
                    self.request_stop_task.emit(tid)

        def _remove_selected(self):
            rows = [
                self.list_widget.row(item)
                for item in self.list_widget.selectedItems()
            ]
            rows.sort(reverse=True)
            for row in rows:
                item = self.list_widget.takeItem(row)
                self._cleanup_item(item)
                del item
            self._update_empty_hint()

        def _clear_finished(self):
            rows = []
            for row in range(self.list_widget.count()):
                item = self.list_widget.item(row)
                data = item.data(Qt.UserRole)
                if data.get("status") in END_STATUS:
                    rows.append(row)
            for row in reversed(rows):
                item = self.list_widget.takeItem(row)
                self._cleanup_item(item)
                del item
            self._update_empty_hint()

        def _cleanup_item(self, item):
            data = item.data(Qt.UserRole)
            if not data:
                return
            norm = data.get("norm")
            tid = data.get("task_id")
            if norm and norm in self._added_paths:
                self._added_paths.remove(norm)
            if norm and norm in self._src_path_to_row:
                del self._src_path_to_row[norm]
            if tid and tid in self._task_id_to_row:
                del self._task_id_to_row[tid]

        # ---------- 日志对话框 ----------
        def _open_log_dialog(self, task_id):
            # 关闭旧的日志对话框
            if self._log_dialog is not None:
                self._log_dialog.close()

            dialog = LogDialog(task_id, self._icons, self)
            dialog.refresh_requested.connect(self._request_log)
            self._worker.log_ready.connect(dialog.on_log_ready, Qt.QueuedConnection)
            self._worker.log_error.connect(dialog.on_log_error, Qt.QueuedConnection)
            dialog.finished.connect(lambda: self._on_log_dialog_closed(dialog))

            self._log_dialog = dialog
            dialog.show()
            self.request_get_log.emit(task_id)

        def _request_log(self, task_id):
            self.request_get_log.emit(task_id)

        def _on_log_dialog_closed(self, dialog):
            if dialog is self._log_dialog:
                try:
                    self._worker.log_ready.disconnect(dialog.on_log_ready)
                except TypeError:
                    if PRINT_ERROR: traceback.print_exc()
                    pass
                try:
                    self._worker.log_error.disconnect(dialog.on_log_error)
                except TypeError:
                    if PRINT_ERROR: traceback.print_exc()
                    pass
                self._log_dialog = None
                dialog.deleteLater()

        # ---------- 关闭 ----------
        def closeEvent(self, event):
            self.request_shutdown.emit()
            if hasattr(self, "_thread"):
                self._thread.wait(5000)
            event.accept()

    # 主函数
    mp.freeze_support()
    app = QApplication(sys.argv)
    try:
        window = MainWindow()
    except FileNotFoundError as e:
        if PRINT_ERROR: traceback.print_exc()
        QMessageBox.critical(None, "启动失败", str(e))
        sys.exit(1)
    sys.exit(app.exec_())



