import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import "./App.css";
import PanelEstadisticas from "./PanelEstadisticas";


//datos que recibimos desde FastAPI
interface Proyecto {
  id: number;
  nombre: string;
  url_repositorio: string;
}

interface Analisis {
  id: number;
  proyecto_id: number;
  estado: string;
}

interface Vulnerabilidad {
  id: number;
  analisis_id: number;
  herramienta: string;
  regla: string;
  archivo: string;
  linea: number;
  mensaje: string;
  severidad: string;
}

function App() {

  //ESTADOS DE LOS PROYECTOS
  const [proyectos, setProyectos] = useState <Proyecto[]>([]);
  const [proyectoId, setProyectoId] = useState <number | null>(null);


  //ESTADOS DE LOS ANÁLISIS
  const [analisis, setAnalisis] = useState <Analisis[]>([]);
  const [analisisId, setAnalisisId] = useState <number | null>(null);


  //VULNERABILIDADES
  const [vulnerabilidades, setVulnerabilidades] = useState <Vulnerabilidad[]>([]);


  //MENSAJES Y CARGA
  const [mensaje, setMensaje] = useState("");
  const [cargando, setCargando] = useState(false);


  //FORMULARIO PARA CREAR PROYECTOS
  const [nombreProyecto, setNombreProyecto] = useState("");
  const [urlRepositorio, setUrlRepositorio] = useState("");
  const [creandoProyecto, setCreandoProyecto] = useState(false);


  //FILTROS DE VULNERABILIDADES
  const [filtroHerramienta, setFiltroHerramienta] = useState("todas");
  const [filtroSeveridad, setFiltroSeveridad] = useState("todas");

  //controlamos cuándo se está eliminando un proyecto
  const [eliminandoProyecto, setEliminandoProyecto] = useState(false);





  //1-CARGAR PROYECTOS AL ABRIR LA PÁGINA
  useEffect(() => {
    async function cargarProyectos() {
      try {
        const respuesta = await fetch("/api/proyectos");

        if (!respuesta.ok) {
          throw new Error("Error al consultar proyectos");
        }

        const datos: Proyecto[] = await respuesta.json();

        setProyectos(datos);
        setProyectoId(datos[0]?.id ?? null);
      } catch {
        setMensaje("No se pudieron cargar los proyectos.");
      }
    }

    void cargarProyectos();
  }, []);




  //2-CARGAR ANÁLISIS CUANDO CAMBIAMOS DE PROYECTO
  useEffect(() => {
    let cancelado = false;

    async function cargarAnalisis() {
      setAnalisis([]);
      setAnalisisId(null);
      setVulnerabilidades([]);

      if (proyectoId === null) return;

      try {
        const respuesta = await fetch(
          `/api/proyectos/${proyectoId}/analisis`
        );

        if(!respuesta.ok) {
          throw new Error("Error al consultar análisis");
        }

        const datos: Analisis[] = await respuesta.json();

        if(!cancelado) {
          setAnalisis(datos);
          setAnalisisId(datos[0]?.id ?? null);
        }
      }catch{
        if(!cancelado) {
          setMensaje("No se pudieron cargar los análisis.");
        }
      }
    }

    void cargarAnalisis();

    return () => {
      cancelado = true;
    };
  }, [proyectoId]);




  //3-CARGAR VULNERABILIDADES DEL ANÁLISIS SELECCIONADO
  useEffect(() => {
    let cancelado = false;

    async function cargarVulnerabilidades() {
      setVulnerabilidades([]);

      if (analisisId === null) return;

      try {
        const respuesta = await fetch(
          `/api/proyectos/analisis/${analisisId}/vulnerabilidades`
        );

        if (!respuesta.ok) {
          throw new Error("Error al consultar vulnerabilidades");
        }

        const datos = await respuesta.json();

        if (!cancelado) {
          setVulnerabilidades(datos.vulnerabilidades);
        }
      } catch {
        if (!cancelado) {
          setMensaje("No se pudieron cargar las vulnerabilidades.");
        }
      }
    }

    void cargarVulnerabilidades();

    return () => {cancelado = true;};
  }, [analisisId]);




  //4-CREAR UN PROYECTO NUEVO
  async function crearProyecto(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();

    if (creandoProyecto || cargando) return;

    setCreandoProyecto(true);
    setMensaje("Creando proyecto...");

    try {
      const respuesta = await fetch("/api/proyectos", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          nombre: nombreProyecto.trim(),
          url_repositorio: urlRepositorio.trim(),
        }),
      });

      if (!respuesta.ok) {
        throw new Error("No se pudo crear el proyecto");
      }

      const nuevo: Proyecto = await respuesta.json();

      //añadimos el nuevo proyecto a la lista
      setProyectos((anteriores) => [...anteriores, nuevo]);

      //seleccionamos el proyecto recién creado
      setProyectoId(nuevo.id);

      //limpiamos el formulario
      setNombreProyecto("");
      setUrlRepositorio("");

      setMensaje(`Proyecto "${nuevo.nombre}" creado correctamente.`);
    } catch (error) {
      setMensaje(
        error instanceof Error ? error.message : "Error al crear proyecto"
      );
    } finally {
      setCreandoProyecto(false);
    }
  }




  //ELIMINAR UN PROYECTO Y SUS ANÁLISIS
  async function eliminarProyecto() {

    //no permitimos eliminar mientras hay operaciones activas
    if (
      proyectoId === null ||
      cargando ||
      creandoProyecto ||
      eliminandoProyecto
    ) {
      return;
    }

    //obtenemos el proyecto seleccionado
    const proyecto = proyectos.find(
      (item) => item.id === proyectoId
    );

    if (!proyecto) return;

    //pedimos confirmación antes de borrar
    const confirmado = window.confirm(
      `¿Eliminar el proyecto "${proyecto.nombre}"?\n\n` +
      "También se eliminarán todos sus análisis y " +
      "vulnerabilidades.\n\n" +
      "Esta acción no se puede deshacer."
    );

    if (!confirmado) return;

    setEliminandoProyecto(true);
    setMensaje(`Eliminando "${proyecto.nombre}"...`);

    try {
      // Solicitamos la eliminación al backend
      const respuesta = await fetch(`/api/proyectos/${proyecto.id}`, {method: "DELETE"}
      );

      if (!respuesta.ok) {
        // Intentamos mostrar el error real de FastAPI
        const error = await respuesta.json().catch(() => null);

        throw new Error(error?.detail ?? "No se pudo eliminar el proyecto");
      }

      //quitamos el proyecto eliminado de la lista
      const restantes = proyectos.filter(
        (item) => item.id !== proyecto.id
      );

      setProyectos(restantes);

      //limpiamos los datos del proyecto eliminado
      setAnalisis([]);
      setAnalisisId(null);
      setVulnerabilidades([]);

      //seleccionamos otro proyecto, si existe
      setProyectoId(restantes[0]?.id ?? null);

      setMensaje(`Proyecto "${proyecto.nombre}" eliminado correctamente`);

    } catch (error) {
      setMensaje(
        error instanceof Error
          ? error.message
          : "Error al eliminar el proyecto"
      );

    } finally {
      setEliminandoProyecto(false);
    }
  }




  //5-EJECUTAR UN ANÁLISIS NUEVO
  async function ejecutarAnalisis() {
    if (proyectoId === null || cargando || creandoProyecto) return;

    setCargando(true);
    setMensaje("Ejecutando Semgrep, Gitleaks y Trivy...");

    try {
      //creamos el registro del análisis en PostgreSQL
      const creacion = await fetch(
        `/api/proyectos/${proyectoId}/analisis`,
        { method: "POST" }
      );

      if (!creacion.ok) {
        throw new Error("No se pudo crear el análisis");
      }

      const nuevo: Analisis = await creacion.json();

      //ejecutamos los escáneres
      const ejecucion = await fetch(
        `/api/proyectos/analisis/${nuevo.id}/ejecutar`,
        { method: "POST" }
      );

      if (!ejecucion.ok) {
        throw new Error("Error durante el escaneo");
      }

      //actualizamos el historial de análisis
      const respuesta = await fetch(
        `/api/proyectos/${proyectoId}/analisis`
      );

      if (!respuesta.ok) {
        throw new Error("No se pudo actualizar el historial");
      }

      const datos: Analisis[] = await respuesta.json();

      setAnalisis(datos);
      setAnalisisId(nuevo.id);

      //consultamos los nuevos hallazgos
      const hallazgos = await fetch(
        `/api/proyectos/analisis/${nuevo.id}/vulnerabilidades`
      );

      if (!hallazgos.ok) {
        throw new Error("No se pudieron consultar los resultados");
      }

      const resultado = await hallazgos.json();

      setVulnerabilidades(resultado.vulnerabilidades);

      setMensaje(`¡Análisis ${nuevo.id} completado correctamente!`);
    } catch (error) {
      setMensaje(
        error instanceof Error
          ? error.message
          : "Error al ejecutar el análisis"
      );
    } finally {
      setCargando(false);
    }
  }




  //6-CONTAR HALLAZGOS POR HERRAMIENTA
  const contar = (herramienta: string) => vulnerabilidades.filter((v) => v.herramienta.toLowerCase() === herramienta).length;




  //7-FILTRAR VULNERABILIDADES
  const vulnerabilidadesFiltradas = vulnerabilidades.filter((v) => {
    const coincideHerramienta =
      filtroHerramienta === "todas" ||
      v.herramienta.toLowerCase() === filtroHerramienta;

    const coincideSeveridad =
      filtroSeveridad === "todas" ||
      v.severidad.toUpperCase() === filtroSeveridad;

    return coincideHerramienta && coincideSeveridad;
  });




  //8-CONTAR SEVERIDADES
  const totalErrores = vulnerabilidades.filter((v) =>
    ["ERROR", "CRITICAL", "HIGH"].includes(v.severidad.toUpperCase())
  ).length;

  const totalAdvertencias = vulnerabilidades.filter((v) =>
    ["WARNING", "MEDIUM"].includes(v.severidad.toUpperCase())
  ).length;




  //9-INTERFAZ DEL DASHBOARD
  return (

    <div className="dashboard">

      {/* CABECERA PRINCIPAL DE REPORADAR */}
      <header className="reporadar-header">

        <div className="header-contenido">

          <div className="header-etiqueta">
            <span className="punto-activo"></span>
            DEVSECOPS WORKSPACE
          </div>

          <h1 className="header-titulo">
            Repo<span>Radar</span>
          </h1>

          <h2 className="header-subtitulo">
            Tu código, bajo el radar.
          </h2>

          <p className="header-descripcion">
            Analiza repositorios de GitHub, detecta posibles
            vulnerabilidades y consulta los resultados
            desde un único lugar.
          </p>

          <div className="header-herramientas">
            <span>✓ Semgrep</span>
            <span>✓ Gitleaks</span>
            <span>✓ Trivy</span>
          </div>

        </div>

        {/* RADAR ANIMADO DECORATIVO */}
        <div className="radar-contenedor" aria-hidden="true">

          <div className="radar-circulo radar-exterior">
            <div className="radar-circulo radar-medio">
              <div className="radar-circulo radar-interior"></div>
            </div>

            <div className="radar-barrido"></div>
            <div className="radar-centro"></div>
            <div className="radar-punto radar-punto-1"></div>
            <div className="radar-punto radar-punto-2"></div>
            <div className="radar-punto radar-punto-3"></div>

          </div>

        </div>

      </header>


      {/*CREAR PROYECTOS */}
      <section className="panel">
        <h3>➕ Crear nuevo proyecto</h3>

        <form onSubmit={crearProyecto} className="formulario-proyecto">
          <input
            type="text"
            placeholder="Nombre del proyecto"
            value={nombreProyecto}
            onChange={(e) => setNombreProyecto(e.target.value)}
            maxLength={100}
            required
          />

          <input
            type="url"
            placeholder="https://github.com/usuario/repositorio"
            value={urlRepositorio}
            onChange={(e) => setUrlRepositorio(e.target.value)}
            required
          />

          <button type="submit" disabled={creandoProyecto || cargando}>
            {creandoProyecto ? "Creando..." : "Crear proyecto"}
          </button>
        </form>
      </section>





      {/* SELECCIONAR, ANALIZAR Y ELIMINAR PROYECTOS */}
      <section className="panel">
        <h3>Proyectos</h3>

        <select
          value={proyectoId ?? ""}
          onChange={(e) => setProyectoId(Number(e.target.value))}
          disabled={
            cargando ||
            creandoProyecto ||
            eliminandoProyecto ||
            proyectos.length === 0
          }
        >
          {proyectos.length === 0 && (
            <option value="">Sin proyectos</option>
          )}

          {proyectos.map((proyecto) => (
            <option key={proyecto.id} value={proyecto.id}>
              #{proyecto.id} — {proyecto.nombre}
            </option>
          ))}
        </select>

        <div className="acciones-proyecto">
          <button
            onClick={() => void ejecutarAnalisis()}
            disabled={
              cargando ||
              creandoProyecto ||
              eliminandoProyecto ||
              proyectoId === null
            }
          >
            {cargando
              ? "Analizando..."
              : "▶ Ejecutar análisis"}
          </button>

          <button
            type="button"
            className="boton-eliminar"
            onClick={() => void eliminarProyecto()}
            disabled={
              cargando ||
              creandoProyecto ||
              eliminandoProyecto ||
              proyectoId === null
            }
          >
            {eliminandoProyecto
              ? "Eliminando..."
              : "🗑️ Eliminar proyecto"}
          </button>
        </div>
      </section>




      {/* MENSAJES */}
      {mensaje && <p className="mensaje">{mensaje}</p>}



      {/* MÉTRICAS DE LOS TRES MOTORES */}
      <div className="tarjetas">
        <div className="tarjeta">
          <h3>Semgrep</h3>
          <strong>{contar("semgrep")}</strong>
          <p>Hallazgos de código</p>
        </div>

        <div className="tarjeta">
          <h3>Gitleaks</h3>
          <strong>{contar("gitleaks")}</strong>
          <p>Posibles secretos</p>
        </div>

        <div className="tarjeta">
          <h3>Trivy</h3>
          <strong>{contar("trivy")}</strong>
          <p>Vulnerabilidades en dependencias</p>
        </div>
      </div>



      {/*GRÁFICAS E HISTORIAL DE ANÁLISIS*/}
      <PanelEstadisticas
        vulnerabilidades={vulnerabilidades}
        analisis={analisis}
        analisisId={analisisId}
        seleccionarAnalisis={setAnalisisId}
      />




      {/* RESUMEN DE SEVERIDADES */}
      <div className="resumen-severidades">
        <div className="resumen-error">
          <strong>{totalErrores}</strong>
          <span>Hallazgos de severidad alta o ERROR</span>
        </div>

        <div className="resumen-warning">
          <strong>{totalAdvertencias}</strong>
          <span>Advertencias y severidad media</span>
        </div>
      </div>

      {/* HISTORIAL Y VULNERABILIDADES */}
      <section className="panel">
        <h3>Análisis disponibles</h3>

        <select
          value={analisisId ?? ""}
          onChange={(e) => setAnalisisId(Number(e.target.value))}
          disabled={cargando || analisis.length === 0}
        >
          {analisis.length === 0 && (
            <option value="">Sin análisis</option>
          )}

          {analisis.map((item) => (
            <option key={item.id} value={item.id}> Análisis #{item.id} — {item.estado} </option>
          ))}
        </select>

        <h3>Vulnerabilidades detectadas: {vulnerabilidades.length}</h3>

        {/* FILTROS */}
        <div className="filtros-seguridad">
          <label>
            Herramienta
            <select
              value={filtroHerramienta}
              onChange={(e) => setFiltroHerramienta(e.target.value)}
            >
              <option value="todas">Todas</option>
              <option value="semgrep">Semgrep</option>
              <option value="gitleaks">Gitleaks</option>
              <option value="trivy">Trivy</option>
            </select>
          </label>

          <label>
            Severidad
            <select
              value={filtroSeveridad}
              onChange={(e) => setFiltroSeveridad(e.target.value)}
            >
              <option value="todas">Todas</option>
              <option value="ERROR">ERROR</option>
              <option value="WARNING">WARNING</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
              <option value="INFO">INFO</option>
              <option value="UNKNOWN">UNKNOWN</option>
            </select>
          </label>
        </div>

        <p className="contador-resultados">
          Mostrando {vulnerabilidadesFiltradas.length} de{" "}
          {vulnerabilidades.length} hallazgos
        </p>

        {/* TABLA DE VULNERABILIDADES */}
        <div className="tabla-contenedor">
          <table>
            <thead>
              <tr>
                <th>Herramienta</th>
                <th>Regla / CVE</th>
                <th>Archivo</th>
                <th>Severidad</th>
              </tr>
            </thead>

            <tbody>
              {vulnerabilidadesFiltradas.map((v) => (
                <tr key={v.id}>
                  <td>{v.herramienta}</td>

                  <td>
                    <details className="detalle-hallazgo">
                      <summary>{v.regla}</summary>

                      <div className="contenido-detalle">
                        <p><strong>Descripción:</strong> {v.mensaje}</p>
                        <p><strong>Archivo:</strong> {v.archivo}</p>
                        <p><strong>Línea:</strong>{" "} {v.linea > 0 ? v.linea : "No aplica"}</p>
                        <p><strong>Herramienta:</strong> {v.herramienta}</p>
                      </div>
                    </details>
                  </td>

                  <td>{v.archivo} {v.linea > 0 ? `:${v.linea}` : ""}</td>

                  <td>{v.severidad}</td>
                </tr>
              ))}

              {vulnerabilidadesFiltradas.length === 0 && (
                <tr>
                  <td colSpan={4}>
                    No hay vulnerabilidades para este filtro.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

export default App;
