import { useState } from 'react'
import { Link } from 'react-router-dom'
import { trackingApi } from '@/api/tracking'

type ForgetState = 'idle' | 'working' | 'done' | 'error'

const Item = ({ title, children }: { title: string; children: React.ReactNode }) => (
  <section className="mb-8">
    <h2 className="text-xl font-bold text-text mb-3">{title}</h2>
    <div className="text-text-secondary space-y-3">{children}</div>
  </section>
)

export const PrivacyPage = () => {
  const [state, setState] = useState<ForgetState>('idle')

  const forgetMe = async () => {
    setState('working')
    try {
      await trackingApi.forgetMe()
      setState('done')
    } catch {
      setState('error')
    }
  }

  return (
    <div className="min-h-screen py-16 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-3xl">
        <h1 className="text-3xl sm:text-4xl font-bold text-text mb-4">Privacidad y medición</h1>
        <p className="text-text-secondary mb-10">
          Este sitio mide cómo se usa para mejorar su contenido. Aquí está lo que se mide, lo que no, y cómo borrar tus datos cuando quieras.
        </p>

        <Item title="Qué se mide">
          <p>
            Las páginas que visitas, el tiempo que la pestaña está activa, hasta dónde bajas, los enlaces externos y descargas que abres,
            si envías el formulario de contacto, qué proyectos abres y qué tan rápido carga la página.
          </p>
          <p>
            También el tipo de navegador, sistema y dispositivo, de qué sitio llegaste (y la campaña, si el enlace la trae) y tu ubicación
            aproximada (país, región y ciudad), que Cloudflare deduce de tu conexión.
          </p>
        </Item>

        <Item title="Qué no se hace">
          <p>
            No se guarda tu dirección IP, no se usan cookies de terceros ni publicidad, no se comparten los datos y no se registra tu
            nombre ni tu correo.
          </p>
        </Item>

        <Item title="Tu identificador">
          <p>
            Para reconocer que vuelves, el navegador guarda un código aleatorio en su almacenamiento local. No te identifica por nombre.
          </p>
          <p>
            Si tu navegador envía la señal <em>Do Not Track</em> o <em>Global Privacy Control</em>, no se guarda ese código: solo se usa
            uno temporal que desaparece al cerrar la pestaña.
          </p>
        </Item>

        <Item title="Cuánto tiempo se guardan">
          <p>Los registros se conservan de forma prolongada para poder ver tendencias. Puedes borrar los tuyos en cualquier momento.</p>
        </Item>

        <Item title="Borrar mis datos">
          <p>
            Este botón borra del servidor todo lo asociado al identificador de este navegador (visitas y eventos) y genera uno nuevo.
            Si usas varios navegadores o dispositivos, hazlo en cada uno.
          </p>
          <button type="button" className="btn px-6 py-2 font-semibold" onClick={forgetMe} disabled={state === 'working'}>
            {state === 'working' ? 'Borrando…' : 'Borrar mis datos'}
          </button>
          <div role="status" aria-live="polite">
            {state === 'done' && <p className="text-text">Listo: se borraron los registros asociados a este navegador, si los había.</p>}
            {state === 'error' && <p className="text-red-500">No se pudo completar el borrado. Inténtalo de nuevo o escríbeme desde la página de contacto.</p>}
          </div>
        </Item>

        <p className="text-text-secondary">
          ¿Dudas? Escríbeme desde <Link to="/contact" className="text-primary font-medium">Contacto</Link>.
        </p>
      </div>
    </div>
  )
}
