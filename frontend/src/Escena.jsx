import { forwardRef, useEffect, useImperativeHandle, useRef } from 'react'
import Phaser from 'phaser'
import Escenario from './escena/Escenario'
import { H, W } from './escena/fondos'

/** Lienzo de Phaser con la escena del juego. Se crea una sola vez y se actualiza por estado. */
const Escena = forwardRef(function Escena({ estado }, ref) {
  const contenedor = useRef(null)
  const juego = useRef(null)

  useEffect(() => {
    juego.current = new Phaser.Game({
      type: Phaser.AUTO,
      parent: contenedor.current,
      width: W,
      height: H,
      backgroundColor: '#dceef2',
      scene: Escenario,
      scale: { mode: Phaser.Scale.FIT, autoCenter: Phaser.Scale.CENTER_BOTH },
      render: { antialias: true },
      audio: { noAudio: true },
      banner: false,
    })
    return () => { juego.current?.destroy(true); juego.current = null }
  }, [])

  useEffect(() => {
    const g = juego.current
    if (!g || !estado) return
    g.registry.set('estado', estado)
    g.scene.keys?.escenario?.aplicar(estado)
  }, [estado])

  useImperativeHandle(ref, () => ({
    reaccion: (clasificacion, delta) => juego.current?.scene.keys?.escenario?.reaccion(clasificacion, delta),
  }), [])

  return <div className="escena" ref={contenedor} role="img" aria-label="Escena del juego" />
})

export default Escena
