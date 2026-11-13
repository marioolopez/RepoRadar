
import "./PanelEstadisticas.css";

//datos que recibe este componente desde App.tsx
interface Vulnerabilidad {
  id: number;
  herramienta: string;
  severidad: string;
}

interface Analisis {
  id: number;
  proyecto_id: number;
  estado: string;
}

interface Props {
  vulnerabilidades: Vulnerabilidad[];
  analisis: Analisis[];
  analisisId: number | null;
  seleccionarAnalisis: (id: number) => void;
}

//componente reutilizable para mostrar una barra
function Barra({
  etiqueta,
  cantidad,
  maximo,
  color,
}: {
  etiqueta: string;
  cantidad: number;
  maximo: number;
  color: string;
}) {
  const porcentaje =
    maximo > 0 ? (cantidad / maximo) * 100 : 0;

  return (
    <div className="estadistica-barra">
      <div className="estadistica-etiqueta">
        <span>{etiqueta}</span>
        <strong>{cantidad}</strong>
      </div>

      <div className="estadistica-pista">
        <div
          className="estadistica-relleno"
          style={{
            width: `${porcentaje}%`,
            backgroundColor: color,
          }}
        />
      </div>
    </div>
  );
}

function PanelEstadisticas({
  vulnerabilidades,
  analisis,
  analisisId,
  seleccionarAnalisis,
}: Props) {
  //cuento los resultados por motor
  const herramientas = [
    { nombre: "Semgrep", color: "#2dd4bf" },
    { nombre: "Gitleaks", color: "#60a5fa" },
    { nombre: "Trivy", color: "#a78bfa" },
  ];

  const datosHerramientas = herramientas.map((herramienta) => ({
    ...herramienta,
    cantidad: vulnerabilidades.filter(
      (v) =>
        v.herramienta.toLowerCase() ===
        herramienta.nombre.toLowerCase()
    ).length,
  }));

  //agrupo las severidades para la visualización
  const niveles = [
    {
      nombre: "Crítica / Alta / Error",
      valores: ["CRITICAL", "HIGH", "ERROR"],
      color: "#f87171",
    },
    {
      nombre: "Media / Advertencia",
      valores: ["MEDIUM", "WARNING"],
      color: "#fbbf24",
    },
    {
      nombre: "Baja / Informativa",
      valores: ["LOW", "INFO"],
      color: "#60a5fa",
    },
    {
      nombre: "Desconocida",
      valores: ["UNKNOWN"],
      color: "#94a3b8",
    },
  ];

  const datosSeveridad = niveles.map((nivel) => ({
    ...nivel,
    cantidad: vulnerabilidades.filter((v) =>
      nivel.valores.includes(v.severidad.toUpperCase())
    ).length,
  }));

  const maximoHerramientas = Math.max(
    1,
    ...datosHerramientas.map((dato) => dato.cantidad)
  );

  const maximoSeveridad = Math.max(
    1,
    ...datosSeveridad.map((dato) => dato.cantidad)
  );

  const completados = analisis.filter(
    (item) => item.estado === "completado"
  ).length;

  const fallidos = analisis.filter(
    (item) => item.estado === "fallido"
  ).length;

  return (
    <section className="estadisticas">
      <div className="estadisticas-cabecera">
        <h2>Estadísticas de seguridad</h2>
        <p>
          Resultados del análisis seleccionado e historial del proyecto.
        </p>
      </div>

      <div className="estadisticas-resumen">
        <div className="estadisticas-metrica">
          <span>Hallazgos</span>
          <strong>{vulnerabilidades.length}</strong>
        </div>

        <div className="estadisticas-metrica">
          <span>Análisis completados</span>
          <strong>{completados}</strong>
        </div>

        <div className="estadisticas-metrica">
          <span>Análisis fallidos</span>
          <strong>{fallidos}</strong>
        </div>
      </div>

      <div className="estadisticas-graficas">
        <article className="estadisticas-panel">
          <h3>Hallazgos por herramienta</h3>

          {datosHerramientas.map((dato) => (
            <Barra
              key={dato.nombre}
              etiqueta={dato.nombre}
              cantidad={dato.cantidad}
              maximo={maximoHerramientas}
              color={dato.color}
            />
          ))}
        </article>

        <article className="estadisticas-panel">
          <h3>Hallazgos por severidad</h3>

          {datosSeveridad.map((dato) => (
            <Barra
              key={dato.nombre}
              etiqueta={dato.nombre}
              cantidad={dato.cantidad}
              maximo={maximoSeveridad}
              color={dato.color}
            />
          ))}
        </article>
      </div>

      <article className="estadisticas-panel">
        <h3>Historial de análisis</h3>

        {analisis.length === 0 ? (
          <p className="estadisticas-vacio">
            Todavía no hay análisis para este proyecto.
          </p>
        ) : (
          <div className="estadisticas-historial">
            {analisis.map((item) => (
              <button
                key={item.id}
                type="button"
                className={
                  item.id === analisisId
                    ? "historial-item seleccionado"
                    : "historial-item"
                }
                onClick={() => seleccionarAnalisis(item.id)}
              >
                <span>Análisis #{item.id}</span>

                <span className={`estado-${item.estado}`}>
                  {item.estado}
                </span>
              </button>
            ))}
          </div>
        )}
      </article>
    </section>
  );
}

export default PanelEstadisticas;
