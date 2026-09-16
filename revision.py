from playwright.sync_api import sync_playwright
import base64
pdfjs=open('/home/claude/node_modules/pdfjs-dist/build/pdf.min.js','rb').read()
worker=open('/home/claude/node_modules/pdfjs-dist/build/pdf.worker.min.js','rb').read()
leaf=open('/home/claude/node_modules/leaflet/dist/leaflet.js','rb').read()
lcss=open('/home/claude/node_modules/leaflet/dist/leaflet.css','rb').read()
h2c=open('/home/claude/node_modules/html2canvas/dist/html2canvas.min.js','rb').read()
jspdf=open('/home/claude/node_modules/jspdf/dist/jspdf.umd.min.js','rb').read()
tile=base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAIAAADTED8xAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAAOUlEQVR4nO3BMQEAAADCoPVPbQ0PoAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAB4GxE4AAG3Vb5WAAAAAElFTkSuQmCC")
jpg=base64.b64decode("/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wAALCAAIAAgBAREA/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AKp//2Q==")
SIM = """
() => {
  window.__store={}; window.__subidas=[]; FB.uid='u1';
  const mk=(base)=>({set:(o)=>{window.__store[base]=Object.assign(window.__store[base]||{},o);window.__subidas.push(base);return Promise.resolve()},
    get:()=>Promise.resolve({exists:!!window.__store[base],data:()=>window.__store[base]||{}}),
    delete:()=>{delete window.__store[base];return Promise.resolve()},
    onSnapshot:()=>{},
    collection:(sc)=>({doc:(id)=>mk(base+'/'+sc+'/'+id),
      orderBy:()=>({get:()=>{const r=[];for(const k in window.__store) if(k.indexOf(base+'/'+sc+'/')===0) r.push({id:k.split('/').pop(),data:()=>window.__store[k]});
        return Promise.resolve({empty:r.length===0,forEach:(f)=>r.forEach(f)})}})})});
  FB.db={collection:(c)=>({doc:(t)=>mk(c+'/'+t)})};
  window.ref=()=>mk('clientes/u1');
}
"""
fallos=[]
with sync_playwright() as p:
    b=p.chromium.launch(); ctx=b.new_context(accept_downloads=True,viewport={'width':390,'height':844}); pg=ctx.new_page()
    errs=[]
    pg.on("pageerror",lambda e:errs.append('JS: '+str(e)))
    pg.on("dialog",lambda d:d.accept("nota"))
    def mk_route(ct,bd):
        def f(route):
            route.fulfill(status=200,content_type=ct,body=bd)
        return f
    for u,ct,bd in [("**/pdf.min.js","application/javascript",pdfjs),("**/pdf.worker.min.js","application/javascript",worker),
                    ("**/leaflet.min.js","application/javascript",leaf),("**/leaflet.min.css","text/css",lcss),
                    ("**/html2canvas.min.js","application/javascript",h2c),("**/jspdf.umd.min.js","application/javascript",jspdf)]:
        pg.route(u, mk_route(ct,bd))
    pg.route("**/nominatim.openstreetmap.org/**",lambda r:r.fulfill(status=200,content_type="application/json",body='[{"lat":"43.257","lon":"-2.917"}]'))
    pg.route("**/tile.openstreetmap.org/**",lambda r:r.fulfill(status=200,content_type="image/png",body=tile))
    pg.goto('file:///home/claude/reformas/index.html'); pg.wait_for_timeout(900)
    pg.evaluate(SIM)

    def chk(nombre,cond,extra=''):
        print(('OK  ' if cond else 'FALLA ')+nombre+(' '+str(extra) if extra and not cond else ''))
        if not cond: fallos.append(nombre)

    # 1 pestañas
    for t in ['presupuesto','clientes','mapa','contrato','tarifa','precios','ajustes','ayuda']:
        pg.evaluate(f"()=>ST('{t}')"); pg.wait_for_timeout(200)
        chk('pestaña '+t, pg.evaluate(f"()=>document.getElementById('page-{t}').classList.contains('on')"))
    # 2 presupuesto: dictado -> partidas
    pg.evaluate("()=>ST('presupuesto')")
    pg.fill('#f_nom','Cliente Revision'); pg.fill('#f_dir','Zabalbide 40'); pg.fill('#f_tel','600112233')
    pg.fill('#dictado','cocina de 5 metros: tirar tabique, quitar alicatado, suelo nuevo, instalacion electrica entera')
    pg.evaluate("()=>convertir()"); pg.wait_for_timeout(500)
    chk('dictado crea partidas', pg.evaluate("()=>cur.lineas.length")>0, pg.evaluate("()=>cur.lineas.length"))
    # 3 PDF arquitecto
    pg.set_input_files('#pdfArq','/home/claude/mediciones.pdf'); pg.wait_for_timeout(4000)
    chk('lee mediciones del arquitecto', pg.evaluate("()=>ARQ.med.length")>0, pg.evaluate("()=>ARQ.med.length"))
    chk('panel del arquitecto visible', pg.evaluate("()=>document.getElementById('arqPanel').style.display")=='block')
    n0=pg.evaluate("()=>cur.lineas.length")
    pg.evaluate("()=>addMediciones()"); pg.wait_for_timeout(400)
    chk('añade las partidas al presupuesto', pg.evaluate("()=>cur.lineas.length")>n0)
    # 4 guardar y numeracion
    pg.evaluate("()=>guardar()"); pg.wait_for_timeout(400)
    num1=pg.evaluate("()=>cur.num")
    pg.evaluate("()=>nuevo()")
    chk('el numero avanza', pg.evaluate("()=>cur.num")!=num1, pg.evaluate("()=>cur.num"))
    # 5 clientes
    pg.evaluate("()=>ST('clientes')"); pg.wait_for_timeout(500)
    chk('ficha con botones', 'Fotos de la obra' in pg.inner_text('#listaCli'))
    # 6 mapa
    pg.evaluate("()=>ST('mapa')"); pg.wait_for_timeout(2500)
    chk('chinchetas en el mapa', pg.evaluate("()=>MARCAS.length")>0, pg.eval_on_selector('#mapInfo','e=>e.innerText'))
    # 7 fotos
    pg.set_input_files('#fotoInput',[{'name':'a.jpg','mimeType':'image/jpeg','buffer':jpg}])
    pg.evaluate("()=>{window.__fotoObra=Object.keys(DB.presus)[0];subirFotos(document.getElementById('fotoInput').files)}")
    pg.wait_for_timeout(600)
    chk('pregunta la partida de la foto', 'De qué trabajo' in pg.inner_text('#fotosLista'))
    pg.evaluate("()=>guardarFotos(Object.keys(DB.presus)[0],0)"); pg.wait_for_timeout(1500)
    chk('foto guardada', pg.evaluate("()=>Object.keys(window.__store).some(k=>k.includes('/fotos/'))"))
    pg.evaluate("()=>cerrarFotos()")
    # 8 PDF
    with pg.expect_download(timeout=120000) as dl:
        pg.evaluate("()=>imprimir('todo')")
    dl.value.save_as('/home/claude/rev.pdf')
    chk('genera el PDF', True)
    # 9 agenda y tarifa
    pg.evaluate("()=>{ST('presupuesto');abrirAgenda()}"); pg.wait_for_timeout(300)
    chk('agenda de clientes', 'Cliente Revision' in pg.inner_text('#agLista'))
    pg.evaluate("()=>cerrarAgenda()")
    pg.evaluate("()=>{ST('tarifa');renderTarifa()}"); pg.wait_for_timeout(300)
    chk('tarifa se pinta', len(pg.inner_text('#tarifaBox'))>200)
    # 10 firma guardada en ajustes
    pg.evaluate("()=>{ST('ajustes');fmInit();FM.hay=true;FM.ctx.fillRect(5,5,40,20);fmGuardar()}"); pg.wait_for_timeout(300)
    chk('firma del contratista', pg.evaluate("()=>!!(AJ.firma&&AJ.firma.length>500)"))
    print('--- errores JS:',errs[:5])
    print('--- RESUMEN:', 'todo bien' if not fallos and not errs else ('fallan: '+', '.join(fallos)))
    b.close()
