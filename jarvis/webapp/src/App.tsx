import { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Send, Cpu, MessageSquare, Terminal, ChevronRight } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface Message {
  role: 'user' | 'jarvis';
  content: string;
  timestamp: string;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [state, setState] = useState('IDLE');
  const [isMicEnabled, setIsMicEnabled] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Connect to Jarvis FastAPI Backend
    ws.current = new WebSocket('ws://localhost:8000/ws');

    ws.current.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === 'STATE_UPDATE') {
        setState(msg.data);
      } else if (msg.type === 'WAKE_WORD_DETECTED') {
        // Option to trigger visual focus or feedback
        console.log('Wake word!', msg.data);
      } else if (msg.type === 'JARVIS_RESPONSE') {
        addMessage('jarvis', msg.data);
      } else if (msg.type === 'USER_MESSAGE') {
        addMessage('user', msg.data);
      }
    };

    ws.current.onclose = () => {
      console.log('WS Disconnected. Retrying in 5s...');
      setTimeout(() => window.location.reload(), 5000);
    };

    return () => ws.current?.close();
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const addMessage = (role: 'user' | 'jarvis', content: string) => {
    setMessages(prev => [...prev, {
      role,
      content,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }]);
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userText = input.trim();
    setInput('');
    
    // Optimistic UI update
    // addMessage('user', userText); // main.py will broadcast it back, so maybe redundant?
    // Let's not add it twice. api.py broadcasts it.

    try {
      await fetch('http://localhost:8000/api/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: userText }),
      });
    } catch (err) {
      console.error('Failed to send command:', err);
      addMessage('jarvis', 'I am sorry sir, I am unable to reach the server.');
    }
  };

  const getStatusColor = () => {
    switch (state) {
      case 'LISTENING': return 'border-cyan-400 text-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.5)]';
      case 'THINKING': return 'border-amber-400 text-amber-400 shadow-[0_0_15px_rgba(251,191,36,0.5)]';
      case 'SPEAKING': return 'border-emerald-400 text-emerald-400 shadow-[0_0_15px_rgba(52,211,153,0.5)]';
      default: return 'border-slate-700 text-slate-500';
    }
  };

  return (
    <div className="flex h-screen w-screen bg-jarvis-dark text-slate-200 overflow-hidden">
      {/* Sidebar */}
      <div className="w-80 bg-black/40 border-r border-slate-800 flex flex-col">
        <div className="p-6 border-b border-slate-800 flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-cyan-950 flex items-center justify-center border border-cyan-500/50">
            <Cpu size={18} className="text-cyan-400" />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-white">JARVIS <span className="text-[10px] text-cyan-500 align-top">V3.5</span></h1>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider px-2 mb-4">Quick Links</div>
          <button className="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-slate-800/50 text-slate-400 hover:text-white transition-colors">
            <Terminal size={18} />
            <span className="text-sm">Knowledge Graph</span>
          </button>
          <button className="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-slate-800/50 text-slate-400 hover:text-white transition-colors">
            <MessageSquare size={18} />
            <span className="text-sm">Recent Interactions</span>
          </button>
        </div>

        <div className="p-4 border-t border-slate-800 bg-black/20">
          <div className="flex items-center justify-between px-2">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${state !== 'IDLE' ? 'bg-cyan-500 animate-pulse' : 'bg-slate-600'}`}></div>
              <span className="text-xs text-slate-500 font-medium">{state}</span>
            </div>
            <button 
              onClick={() => setIsMicEnabled(!isMicEnabled)}
              className={`p-1.5 rounded-md transition-all ${isMicEnabled ? 'text-cyan-400 bg-cyan-400/10' : 'text-slate-500 bg-slate-800'}`}
            >
              {isMicEnabled ? <Mic size={16} /> : <MicOff size={16} />}
            </button>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative">
        {/* Arc Reactor background decoration */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 opacity-[0.03] pointer-events-none">
          <div className="w-96 h-96 rounded-full border-[20px] border-cyan-500 flex items-center justify-center">
             <div className="w-64 h-64 rounded-full border-[10px] border-cyan-500 flex items-center justify-center">
                <div className="w-32 h-32 rounded-full border-[5px] border-cyan-500"></div>
             </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-8 space-y-8" ref={scrollRef}>
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center space-y-6 opacity-60">
              <div className={`w-32 h-32 rounded-full border-4 flex items-center justify-center arc-reactor ${state === 'LISTENING' ? 'listening' : ''} ${getStatusColor()}`}>
                <Cpu size={48} />
              </div>
              <div className="text-center">
                <h2 className="text-2xl font-light text-white">How can I assist you today, Sir?</h2>
                <p className="text-slate-500 mt-2">Voice and text interface active.</p>
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2 duration-300`}>
              <div className={`max-w-[80%] p-4 rounded-2xl ${
                msg.role === 'user' 
                  ? 'bg-cyan-600/20 border border-cyan-500/30 text-slate-100 rounded-tr-none' 
                  : 'bg-slate-900 border border-slate-800 text-slate-300 rounded-tl-none'
              }`}>
                <div className="flex items-center justify-between mb-1 gap-4">
                  <span className={`text-[10px] font-bold uppercase tracking-widest ${msg.role === 'user' ? 'text-cyan-400' : 'text-slate-500'}`}>
                    {msg.role === 'user' ? 'You' : 'Jarvis'}
                  </span>
                  <span className="text-[10px] text-slate-600">{msg.timestamp}</span>
                </div>
                <div className="prose prose-invert max-w-none text-sm leading-relaxed">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Input Bar */}
        <div className="p-8">
          <div className="max-w-4xl mx-auto relative group">
            <div className={`absolute inset-0 bg-cyan-500/20 blur-xl transition-opacity duration-500 ${state !== 'IDLE' ? 'opacity-100' : 'opacity-0 group-focus-within:opacity-50'}`}></div>
            <div className="relative bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-2 flex items-center shadow-2xl">
              <div className={`p-3 rounded-xl transition-colors ${getStatusColor()}`}>
                <ChevronRight size={20} />
              </div>
              <input 
                type="text" 
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder={state === 'LISTENING' ? "Listening sir..." : "Send a command..."}
                className="flex-1 bg-transparent border-none focus:ring-0 text-slate-200 placeholder-slate-600 px-4 py-2"
              />
              <button 
                onClick={handleSend}
                disabled={!input.trim()}
                className={`p-3 rounded-xl transition-all ${input.trim() ? 'bg-cyan-500 text-black hover:bg-cyan-400 shadow-lg shadow-cyan-500/20' : 'bg-slate-800 text-slate-500'}`}
              >
                <Send size={20} />
              </button>
            </div>
          </div>
          <div className="text-center mt-4">
             <p className="text-[10px] text-slate-600 uppercase tracking-[0.2em] font-medium">Enhanced Knowledge Retrieval System Active</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
