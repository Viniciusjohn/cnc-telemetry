import { useEffect, useState } from "react";
import { fetchMachineStatus, MachineStatus, ApiError } from "./lib/api";

const MACHINE_ID = "CNC-SIM-001";
const POLL_INTERVAL_MS = 2000;

export default function App() {
  const [status, setStatus] = useState<MachineStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    async function poll() {
      try {
        const data = await fetchMachineStatus(MACHINE_ID);
        if (isMounted) {
          setStatus(data);
          setError(null);
          setIsLoading(false);
        }
      } catch (e) {
        if (isMounted) {
          if (e instanceof ApiError) {
            setError(`HTTP ${e.status}: ${e.message}`);
          } else {
            setError(e instanceof Error ? e.message : "Unknown error");
          }
          setIsLoading(false);
        }
      }
    }

    poll();
    const intervalId = setInterval(poll, POLL_INTERVAL_MS);

    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };
  }, []);

  return (
    <main style={{background:"#0a0a0a", minHeight:"100vh", color:"#e5e7eb", padding:"24px", fontFamily:"ui-sans-serif"}}>
      <header style={{marginBottom:24, display:"flex", justifyContent:"space-between", alignItems:"center"}}>
        <h1 style={{fontSize:28, fontWeight:700}}>CNC Telemetry — Dashboard</h1>
        <div style={{fontSize:14, opacity:0.7}}>
          {status?.machine_id || "—"}
        </div>
      </header>

      {error && (
        <div style={{background:"rgba(220,38,38,0.2)", border:"1px solid #dc2626", borderRadius:8, padding:16, marginBottom:16}}>
          <strong>Erro:</strong> {error}
        </div>
      )}

      {isLoading && !status && (
        <div style={{textAlign:"center", padding:32, opacity:0.5}}>
          Carregando...
        </div>
      )}

      <section style={{display:"grid", gridTemplateColumns:"repeat(auto-fit, minmax(200px, 1fr))", gap:16, maxWidth:1200}}>
        <Card 
          title="RPM" 
          value={status?.rpm.toFixed(1) ?? "—"} 
          suffix="rev/min"
          color={getStateColor(status?.state)}
        />
        <Card 
          title="Feed" 
          value={status?.feed_mm_min.toFixed(1) ?? "—"} 
          suffix="mm/min"
        />
        <Card 
          title="Estado" 
          value={formatState(status?.state)}
          color={getStateColor(status?.state)}
        />
        <Card 
          title="Atualizado" 
          value={status ? formatTime(status.updated_at) : "—"}
        />
      </section>

      <footer style={{marginTop:24, fontSize:12, opacity:0.5, textAlign:"center"}}>
        Polling: {POLL_INTERVAL_MS / 1000}s | API: {import.meta.env.VITE_API_BASE}
      </footer>
    </main>
  );
}

interface CardProps {
  title: string;
  value: string;
  suffix?: string;
  color?: string;
}

function Card({ title, value, suffix, color }: CardProps) {
  return (
    <div style={{background:"#111827", padding:20, borderRadius:16, border:"1px solid #1f2937"}}>
      <div style={{fontSize:12, opacity:0.6, marginBottom:8, textTransform:"uppercase", letterSpacing:"0.05em"}}>
        {title}
      </div>
      <div style={{fontSize:32, fontWeight:700, color: color || "#e5e7eb"}}>
        {value}
      </div>
      {suffix && (
        <div style={{fontSize:12, opacity:0.5, marginTop:4}}>
          {suffix}
        </div>
      )}
    </div>
  );
}

function formatState(state?: string): string {
  if (!state) return "—";
  switch (state) {
    case "running":
      return "RODANDO";
    case "stopped":
      return "PARADA";
    case "idle":
      return "OCIOSA";
    default:
      return state.toUpperCase();
  }
}

function getStateColor(state?: string): string {
  switch (state) {
    case "running":
      return "#10b981"; // green
    case "stopped":
      return "#ef4444"; // red
    case "idle":
      return "#f59e0b"; // yellow
    default:
      return "#e5e7eb"; // gray
  }
}

function formatTime(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleTimeString("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}
