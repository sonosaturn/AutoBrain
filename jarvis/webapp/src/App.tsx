import { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Send, Cpu, ChevronRight, Plus, GraduationCap, History, Settings, Trash2, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface Message {
  role: 'user' | 'jarvis';
  content: string;
  timestamp: string;
}

interface Chat {
  id: string;
  title: string;
  gem: string;
  messages: Message[];
  updated_at: string;
}

interface ModelUsage {
  requests: number;
  limit: number;
}

function App() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [state, setState] = useState('IDLE');
  const [isMicEnabled, setIsMicEnabled] = useState(true);
  const [activeGem, setActiveGem] = useState('default');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [activeModel, setActiveModel] = useState('gemini-3-flash-preview');
  const [usageStats, setUsageStats] = useState<Record<string, ModelUsage>>({});
  const scrollRef = useRef<HTMLDivElement>(null);
  const ws = useRef<WebSocket | null>(null);

  const fetchChats = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8008/api/chats');
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();
      if (Array.isArray(data)) {
        setChats(data);
      } else {
        console.error('Expected array for chats, got:', data);
        setChats([]);
      }
    } catch (err) {
      console.error('Failed to fetch chats:', err);
      setChats([]);
    }
  };

  const fetchConfig = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8008/api/config');
      const data = await res.json();
      setActiveModel(data.active_model);
      setUsageStats(data.usage || {});
    } catch (err) {
      console.error('Failed to fetch config:', err);
    }
  };

  const updateModel = async (model: string) => {
    try {
      await fetch('http://127.0.0.1:8008/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ active_model: model }),
      });
      setActiveModel(model);
      fetchConfig();
    } catch (err) {
      console.error('Failed to update model:', err);
    }
  };

  const deleteChat = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Eliminare questa conversazione?')) return;
    try {
      await fetch(`http://127.0.0.1:8008/api/chats/${id}`, { method: 'DELETE' });
      setChats(chats.filter(c => c.id !== id));
      if (currentChatId === id) {
        setCurrentChatId(null);
        setMessages([]);
      }
    } catch (err) {
      console.error('Failed to delete chat:', err);
    }
  };

  const createNewChat = async (gem: string = 'default') => {
    try {
      const res = await fetch('http://127.0.0.1:8008/api/chats', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: 'New Conversation', gem }),
      });
      const newChat = await res.json();
      setChats([newChat, ...chats]);
      setCurrentChatId(newChat.id);
      setMessages([]);
      setActiveGem(gem);
    } catch (err) {
      console.error('Failed to create chat:', err);
    }
  };

  const loadChat = async (id: string) => {
    try {
      const res = await fetch(`http://127.0.0.1:8008/api/chats/${id}`);
      const chat = await res.json();
      setCurrentChatId(chat.id);
      setMessages(chat.messages);
      setActiveGem(chat.gem);
    } catch (err) {
      console.error('Failed to load chat:', err);
    }
  };

  useEffect(() => {
    fetchChats();
    fetchConfig();
  }, []);

  useEffect(() => {
    let isMounted = true;
    const connectWS = () => {
      if (ws.current?.readyState === WebSocket.OPEN) return;
      const socket = new WebSocket('ws://127.0.0.1:8008/ws');
      socket.onmessage = (event) => {
        if (!isMounted) return;
        const msg = JSON.parse(event.data);
        if (msg.type === 'STATE_UPDATE') {
          setState(msg.data);
        } else if (msg.type === 'JARVIS_RESPONSE') {
          addMessage('jarvis', msg.data);
          fetchChats(); // Refresh sidebar titles
          fetchConfig(); // Refresh usage stats
        } else if (msg.type === 'USER_MESSAGE') {
          addMessage('user', msg.data);
        }
      };
      socket.onclose = () => {
        if (!isMounted) return;
        setTimeout(connectWS, 2000);
      };
      ws.current = socket;
    };
    connectWS();
    return () => {
      isMounted = false;
      ws.current?.close();
    };
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

    // Create a chat if none exists
    let chatId = currentChatId;
    if (!chatId) {
      try {
        const res = await fetch('http://127.0.0.1:8008/api/chats', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: input.trim().substring(0, 20), gem: activeGem }),
        });
        const newChat = await res.json();
        chatId = newChat.id;
        setCurrentChatId(chatId);
      } catch (err) {
         console.error(err);
         return;
      }
    }

    const userText = input.trim();
    setInput('');
    
    try {
      await fetch('http://127.0.0.1:8008/api/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: userText, chat_id: chatId, gem: activeGem }),
      });
    } catch (err) {
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
      {/* Settings Modal */}
      {isSettingsOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-300">
          <div className="bg-slate-900 border border-slate-800 w-[500px] rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-300">
            <div className="p-6 border-b border-slate-800 flex items-center justify-between bg-black/20">
              <div className="flex items-center gap-3">
                <Settings className="text-cyan-400" size={20} />
                <h3 className="text-lg font-bold">System Settings</h3>
              </div>
              <button onClick={() => setIsSettingsOpen(false)} className="text-slate-500 hover:text-white transition-colors">
                <X size={20} />
              </button>
            </div>
            <div className="p-8 space-y-6">
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Active Model</label>
                <select 
                  value={activeModel}
                  onChange={(e) => updateModel(e.target.value)}
                  className="w-full p-3 bg-black/40 border border-slate-800 rounded-xl text-sm font-mono text-cyan-400 focus:ring-1 focus:ring-cyan-500/50 outline-none appearance-none"
                >
                  <option value="gemini-3.1-pro-preview" disabled={usageStats['gemini-3.1-pro-preview']?.requests >= usageStats['gemini-3.1-pro-preview']?.limit}>
                    gemini-3.1-pro-preview {usageStats['gemini-3.1-pro-preview'] && `(${usageStats['gemini-3.1-pro-preview'].requests}/${usageStats['gemini-3.1-pro-preview'].limit})`}
                  </option>
                  <option value="gemini-3.5-flash" disabled={usageStats['gemini-3.5-flash']?.requests >= usageStats['gemini-3.5-flash']?.limit}>
                    gemini-3.5-flash {usageStats['gemini-3.5-flash'] && `(${usageStats['gemini-3.5-flash'].requests}/${usageStats['gemini-3.5-flash'].limit})`}
                  </option>
                  <option value="gemini-3-flash-preview" disabled={usageStats['gemini-3-flash-preview']?.requests >= usageStats['gemini-3-flash-preview']?.limit}>
                    gemini-3-flash-preview {usageStats['gemini-3-flash-preview'] && `(${usageStats['gemini-3-flash-preview'].requests}/${usageStats['gemini-3-flash-preview'].limit})`}
                  </option>
                  <option value="gemini-3.1-flash-lite" disabled={usageStats['gemini-3.1-flash-lite']?.requests >= usageStats['gemini-3.1-flash-lite']?.limit}>
                    gemini-3.1-flash-lite {usageStats['gemini-3.1-flash-lite'] && `(${usageStats['gemini-3.1-flash-lite'].requests}/${usageStats['gemini-3.1-flash-lite'].limit})`}
                  </option>
                  <option value="gemini-1.5-flash" disabled={usageStats['gemini-1.5-flash']?.requests >= usageStats['gemini-1.5-flash']?.limit}>
                    gemini-1.5-flash {usageStats['gemini-1.5-flash'] && `(${usageStats['gemini-1.5-flash'].requests}/${usageStats['gemini-1.5-flash'].limit})`}
                  </option>
                </select>
                <div className="flex justify-between mt-1">
                  <p className="text-[10px] text-slate-500 italic">Changing the model affects both intent parsing and reasoning.</p>
                  {usageStats[activeModel] && (
                    <span className={`text-[10px] font-bold ${usageStats[activeModel].requests > usageStats[activeModel].limit * 0.8 ? 'text-amber-500' : 'text-slate-500'}`}>
                      Quota: {Math.round((usageStats[activeModel].requests / usageStats[activeModel].limit) * 100)}%
                    </span>
                  )}
                </div>
              </div>
              
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Knowledge Graph</label>
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-4 bg-black/20 border border-slate-800 rounded-xl text-center">
                    <div className="text-lg font-bold text-white">3,991</div>
                    <div className="text-[10px] text-slate-500 uppercase">Nodes</div>
                  </div>
                  <div className="p-4 bg-black/20 border border-slate-800 rounded-xl text-center">
                    <div className="text-lg font-bold text-white">8,129</div>
                    <div className="text-[10px] text-slate-500 uppercase">Edges</div>
                  </div>
                </div>
              </div>

              <div className="pt-4 flex justify-end gap-3">
                <button 
                  onClick={() => setIsSettingsOpen(false)}
                  className="px-6 py-2.5 rounded-xl bg-cyan-500 text-black font-bold text-xs hover:bg-cyan-400 transition-all shadow-lg shadow-cyan-500/10"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Sidebar */}
      <div className="w-80 bg-black/40 border-r border-slate-800 flex flex-col">
        <div className="p-6 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-cyan-950 flex items-center justify-center border border-cyan-500/50">
              <Cpu size={18} className="text-cyan-400" />
            </div>
            <h1 className="text-xl font-bold tracking-tight text-white">JARVIS</h1>
          </div>
          <button onClick={() => createNewChat('default')} className="p-2 hover:bg-slate-800 rounded-full transition-colors text-slate-400 hover:text-white">
            <Plus size={20} />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {/* Gems Section */}
          <div>
            <div className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] px-2 mb-3">Specialized Gems</div>
            <button 
              onClick={() => createNewChat('university_tutor')}
              className={`w-full flex items-center gap-3 p-3 rounded-xl transition-all mb-2 ${activeGem === 'university_tutor' ? 'bg-cyan-500/10 border border-cyan-500/30 text-cyan-400' : 'hover:bg-slate-800/50 text-slate-400'}`}
            >
              <GraduationCap size={18} />
              <div className="text-left">
                <div className="text-xs font-bold">University Tutor</div>
                <div className="text-[10px] opacity-60">Academic Assistant</div>
              </div>
            </button>
          </div>

          {/* History Section */}
          <div>
            <div className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] px-2 mb-3">Recent Chats</div>
            <div className="space-y-1">
              {chats.map(chat => (
                <div key={chat.id} className="group relative">
                  <button 
                    onClick={() => loadChat(chat.id)}
                    className={`w-full flex items-center gap-3 p-2.5 rounded-lg text-left transition-all ${currentChatId === chat.id ? 'bg-slate-800 text-white' : 'hover:bg-slate-800/30 text-slate-500 hover:text-slate-300'}`}
                  >
                    <History size={14} className="shrink-0" />
                    <span className="text-xs truncate flex-1 pr-6">{chat.title}</span>
                  </button>
                  <button 
                    onClick={(e) => deleteChat(chat.id, e)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-slate-600 hover:text-rose-500 opacity-0 group-hover:opacity-100 transition-all"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="p-4 border-t border-slate-800 bg-black/20">
          <div className="flex items-center justify-between px-2">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${state !== 'IDLE' ? 'bg-cyan-500 animate-pulse' : 'bg-slate-600'}`}></div>
              <span className="text-xs text-slate-500 font-medium capitalize">{state.toLowerCase()}</span>
            </div>
            <div className="flex gap-1">
              <button onClick={() => setIsSettingsOpen(true)} className={`p-1.5 rounded-md transition-colors ${isSettingsOpen ? 'text-cyan-400 bg-cyan-400/10' : 'text-slate-500 hover:bg-slate-800'}`}>
                <Settings size={14} />
              </button>
              <button 
                onClick={() => setIsMicEnabled(!isMicEnabled)}
                className={`p-1.5 rounded-md transition-all ${isMicEnabled ? 'text-cyan-400 bg-cyan-400/10' : 'text-slate-500 bg-slate-800'}`}
              >
                {isMicEnabled ? <Mic size={14} /> : <MicOff size={14} />}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative">
        <div className="flex-1 overflow-y-auto p-8 space-y-8" ref={scrollRef}>
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center space-y-6 opacity-60">
              <div className={`w-32 h-32 rounded-full border-4 flex items-center justify-center arc-reactor ${state === 'LISTENING' ? 'listening' : ''} ${getStatusColor()}`}>
                {activeGem === 'university_tutor' ? <GraduationCap size={48} /> : <Cpu size={48} />}
              </div>
              <div className="text-center">
                <h2 className="text-2xl font-light text-white">
                  {activeGem === 'university_tutor' ? 'Ready for your University notes, Sir.' : 'How can I assist you today, Sir?'}
                </h2>
                <p className="text-slate-500 mt-2">
                  {activeGem === 'university_tutor' ? 'Specialized Gem: Academic Support Active' : 'Voice and text interface active.'}
                </p>
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2 duration-300`}>
              <div className={`max-w-[80%] p-5 rounded-2xl ${
                msg.role === 'user' 
                  ? 'bg-cyan-600/10 border border-cyan-500/20 text-slate-100 rounded-tr-none' 
                  : 'bg-slate-900 border border-slate-800 text-slate-300 rounded-tl-none shadow-xl'
              }`}>
                <div className="flex items-center justify-between mb-2 gap-4 border-b border-white/5 pb-2">
                  <div className="flex items-center gap-2">
                    {msg.role === 'jarvis' && (activeGem === 'university_tutor' ? <GraduationCap size={12} className="text-cyan-500" /> : <Cpu size={12} className="text-cyan-500" />)}
                    <span className={`text-[10px] font-bold uppercase tracking-widest ${msg.role === 'user' ? 'text-cyan-400' : 'text-slate-500'}`}>
                      {msg.role === 'user' ? 'You' : (activeGem === 'university_tutor' ? 'Tutor' : 'Jarvis')}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-600">{msg.timestamp}</span>
                </div>
                <div className="prose prose-invert max-w-none text-sm leading-relaxed prose-p:my-2">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Input Bar */}
        <div className="p-8 pt-0">
          <div className="max-w-4xl mx-auto relative group">
            <div className={`absolute inset-0 bg-cyan-500/10 blur-2xl transition-opacity duration-500 ${state !== 'IDLE' ? 'opacity-100' : 'opacity-0 group-focus-within:opacity-50'}`}></div>
            <div className="relative bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-2 flex items-center shadow-2xl">
              <div className={`p-3 rounded-xl transition-colors ${getStatusColor()}`}>
                <ChevronRight size={20} />
              </div>
              <input 
                type="text" 
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder={state === 'LISTENING' ? "Listening sir..." : `Ask your ${activeGem === 'university_tutor' ? 'Tutor' : 'assistant'}...`}
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
        </div>
      </div>
    </div>
  );
}

export default App;
