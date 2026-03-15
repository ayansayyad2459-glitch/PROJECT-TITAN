import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { Terminal, Download, Flame, ShieldAlert, Cpu, Database, GitBranch, ChevronRight, Zap, BookOpen, Activity, Server, Wifi, Globe, ShieldCheck, Code, Layers, Box, Lock, User, LogOut } from 'lucide-react';

// --- CUSTOM HOOK: Fixed Cinematic Scroll Reveal ---
const useScrollReveal = (activeTab) => {
    useEffect(() => {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('active-reveal');
                }
            });
        }, { threshold: 0.10 });

        const timeoutId = setTimeout(() => {
            const hiddenElements = document.querySelectorAll('.scroll-reveal, .reveal-left, .reveal-right, .reveal-scale');
            hiddenElements.forEach((el) => observer.observe(el));
        }, 100);

        return () => {
            clearTimeout(timeoutId);
            observer.disconnect();
        };
    }, [activeTab]); 
};

const Dashboard = () => {
    const { user, logout } = useContext(AuthContext);
    
    // --- UI STATES ---
    const [activeTab, setActiveTab] = useState('repoHealer'); 
    const [scrollProgress, setScrollProgress] = useState(0);
    const [isProfileOpen, setIsProfileOpen] = useState(false);
    
    useScrollReveal(activeTab);
    
    // --- BACKEND / REAL DATA STATES ---
    const [tickets, setTickets] = useState([]);
    const [repoUrl, setRepoUrl] = useState('');
    const [crashDesc, setCrashDesc] = useState('');
    const [status, setStatus] = useState('IDLE'); 
    const [downloadLink, setDownloadLink] = useState(null);
    const [terminalLogs, setTerminalLogs] = useState([]);

    const [threatIntel, setThreatIntel] = useState([]);
    const [coreAllocation, setCoreAllocation] = useState([]);
    const [telemetry, setTelemetry] = useState(null);

    // --- SCROLL PROGRESS TRACKER ---
    useEffect(() => {
        const handleScroll = () => {
            const totalScroll = document.documentElement.scrollTop;
            const windowHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
            const scroll = totalScroll / windowHeight;
            setScrollProgress(scroll * 100);
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    // --- DATA FETCHING ---
    const fetchTickets = async () => {
        try {
            const res = await fetch('http://localhost:5000/api/tickets', {
                headers: { Authorization: `Bearer ${user?.token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setTickets(data);
            }
        } catch (err) { console.error("Audit Ledger Fetch Failed", err); }
    };

    // --- DELETE TICKET HANDLER ---
    const handleDeleteTicket = async (ticketId) => {
        if (!window.confirm("⚠️ WARNING: Are you sure you want to permanently purge this record from the Ledger?")) return;
        
        try {
            const res = await fetch(`http://localhost:5000/api/tickets/${ticketId}`, {
                method: 'DELETE',
                headers: { Authorization: `Bearer ${user?.token}` }
            });
            
            if (res.ok) {
                setTickets(prevTickets => prevTickets.filter(t => t._id !== ticketId));
            } else {
                alert("Failed to delete ticket. Is the backend running?");
            }
        } catch (err) {
            console.error("Delete operation failed", err);
        }
    };

    const fetchSystemStats = async () => {
        try {
            const res = await fetch('http://localhost:5000/api/healer/stats', {
                headers: { Authorization: `Bearer ${user?.token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setThreatIntel(data.threatIntel || []);
                setCoreAllocation(data.coreAllocation || []);
                setTelemetry(data.telemetry || null);
            }
        } catch (err) { 
            console.error("Failed to fetch live system stats", err); 
        }
    };

    useEffect(() => { 
        fetchTickets(); 
        fetchSystemStats(); 
    }, []);

    // --- CHAOS MONKEY HANDLER ---
    const triggerChaosMonkey = async () => {
        if(!window.confirm("⚠️ SYSTEM WARNING: Injecting fatal fault into live backend. Proceed?")) return;
        
        try {
            const res = await fetch('http://localhost:5000/api/healer/crash', {
                method: 'POST',
                headers: { Authorization: `Bearer ${user?.token}` }
            });
            
            const data = await res.json();
            
            if (data.error) {
                alert(`🎯 TRAP SUCCESS: ${data.error}`); 
            } else {
                alert("Chaos payload delivered.");
            }

            setTimeout(() => {
                fetchTickets();
                fetchSystemStats();
            }, 1500); 
            
        } catch (err) { 
            console.error("Crash trigger fired", err); 
            alert("Connection severed. Is the backend running?");
        }
    };

    const handleRepoHeal = async (e) => {
        e.preventDefault();
        if(!repoUrl) {
            alert("TITAN CORE WARNING: Provide Target Repository URL.");
            return;
        }
        
        setStatus('WORKING');
        const isFullScan = !crashDesc || crashDesc.trim() === "";
        
        setTerminalLogs(isFullScan 
            ? ["[SYS_INIT] 🚀 Independent Full Repo Scan Initiated...", "[SYS_INIT] Handshaking with GitHub API..."]
            : ["[SYS_INIT] 🚀 Targeted Fix Initiated...", "[SYS_INIT] Handshaking with GitHub API..."]
        );

        const logSequence = isFullScan ? [
            { time: 1000, msg: "Allocating workspace memory & cloning FULL repo..." },
            { time: 3000, msg: "Deploying Swarm for Deep Architecture Scan..." },
            { time: 6000, msg: "Scanning files for vulnerabilities..." },
            { time: 10000, msg: "Markdown generation complete..." },
            { time: 30000, msg: "Archiving complete repository payload..." }
        ] : [
            { time: 1000, msg: "Allocating workspace memory..." },
            { time: 3000, msg: "Deploying Language-Agnostic Agentic Swarm..." },
            { time: 30000, msg: "Archiving DevSecOps payload..." }
        ];

        logSequence.forEach(log => {
            setTimeout(() => { setTerminalLogs(prev => [...prev, log.msg]); }, log.time);
        });
        
        try {
            const res = await fetch('http://localhost:5000/api/healer/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${user?.token}` },
                body: JSON.stringify({ repoUrl, crashDescription: isFullScan ? "FULL_REPO_SCAN" : crashDesc })
            });

            if (res.ok) {
                setTimeout(() => {
                    setTerminalLogs(prev => [...prev, "MISSION COMPLETE. Payload ready."]);
                    setStatus('SUCCESS');
                    const repoName = repoUrl.split('/').pop().replace('.git', '');
                    setDownloadLink(`http://localhost:5000/downloads/${repoName}-titan-fix-latest.zip`);
                    fetchTickets(); 
                    fetchSystemStats();
                }, 32000); 
            }
        } catch (error) { 
            setStatus('IDLE'); 
            setTerminalLogs(["[FATAL] Connection severed."]);
        }
    };

    const defaultAllocation = [
        { label: 'GPU Swarm Processing', val: '0%', color: 'bg-blue-500', shadow: 'shadow-[0_0_15px_#3b82f6]' },
        { label: 'Sandbox Memory Allocation', val: '0%', color: 'bg-purple-500', shadow: 'shadow-[0_0_15px_#a855f7]' },
        { label: 'GitHub API Uplink', val: '0%', color: 'bg-cyan-500', shadow: 'shadow-[0_0_15px_#06b6d4]' }
    ];

    const activeAllocation = coreAllocation.length > 0 ? coreAllocation : defaultAllocation;

    return (
        <div className="bg-[#020202] min-h-screen text-white font-sans selection:bg-blue-500/30 overflow-x-hidden relative">
            <div className="fixed top-0 left-0 h-[3px] bg-gradient-to-r from-cyan-400 to-blue-600 z-[100] transition-all duration-150 ease-out shadow-[0_0_15px_rgba(6,182,212,0.8)]" style={{ width: `${scrollProgress}%` }}></div>

            <style dangerouslySetInnerHTML={{__html: `
                .glow-orb { filter: blur(140px); opacity: 0.5; animation: pulse-orb 8s alternate infinite ease-in-out; }
                @keyframes pulse-orb { 0% { transform: scale(1); opacity: 0.3; } 100% { transform: scale(1.2); opacity: 0.6; } }
                .scroll-reveal { opacity: 0; transform: translateY(60px); transition: all 1s cubic-bezier(0.16, 1, 0.3, 1); }
                .reveal-left { opacity: 0; transform: translateX(-80px); transition: all 1s cubic-bezier(0.16, 1, 0.3, 1); }
                .reveal-right { opacity: 0; transform: translateX(80px); transition: all 1s cubic-bezier(0.16, 1, 0.3, 1); }
                .reveal-scale { opacity: 0; transform: scale(0.9); transition: all 1s cubic-bezier(0.16, 1, 0.3, 1); }
                .active-reveal { opacity: 1 !important; transform: translate(0, 0) scale(1) !important; }
                .glass-nav { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); }
                .glass-panel { background: rgba(255, 255, 255, 0.02); backdrop-filter: blur(30px); border: 1px solid rgba(255, 255, 255, 0.05); }
                @keyframes scanline { 0% { transform: translateY(-100%); } 100% { transform: translateY(100%); } }
                .animate-scanline { animation: scanline 3s linear infinite; }
                .fade-in-up { animation: fadeInUp 0.5s ease-out forwards; }
                @keyframes fadeInUp { 0% { opacity: 0; transform: translateY(20px); } 100% { opacity: 1; transform: translateY(0); } }
            `}} />

            <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
                <div className="absolute top-[-10%] left-[-10%] w-[60vw] h-[60vw] bg-blue-600 rounded-full glow-orb"></div>
                <div className="absolute bottom-[-20%] right-[-10%] w-[50vw] h-[50vw] bg-cyan-600 rounded-full glow-orb" style={{animationDelay: '-4s'}}></div>
            </div>

            <nav className="fixed top-6 left-1/2 -translate-x-1/2 w-[95%] max-w-7xl glass-nav rounded-full px-4 py-3 flex justify-between items-center z-50">
                <div className="flex items-center gap-3 pl-2">
                    <div className="bg-white text-black p-1.5 rounded-full"><Terminal className="w-5 h-5" /></div>
                    <span className="font-black tracking-widest text-lg">TITAN<span className="text-blue-500">.CORE</span></span>
                </div>
                
                <div className="flex items-center gap-2">
                    <button onClick={() => setActiveTab('repoHealer')} className={`px-4 py-2 rounded-full text-xs font-bold uppercase tracking-widest transition-all ${activeTab === 'repoHealer' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.3)]' : 'text-gray-400 hover:text-white'}`}><Cpu className="w-4 h-4 inline mr-2" />Healer</button>
                    <button onClick={() => setActiveTab('ledger')} className={`px-4 py-2 rounded-full text-xs font-bold uppercase tracking-widest transition-all ${activeTab === 'ledger' ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50 shadow-[0_0_15px_rgba(6,182,212,0.3)]' : 'text-gray-400 hover:text-white'}`}><Database className="w-4 h-4 inline mr-2" />Ledger</button>
                    <button onClick={() => setActiveTab('chaos')} className={`px-4 py-2 rounded-full text-xs font-bold uppercase tracking-widest transition-all ${activeTab === 'chaos' ? 'bg-red-500/20 text-red-400 border border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.3)]' : 'text-gray-400 hover:text-white'}`}><Flame className="w-4 h-4 inline mr-2" />Chaos</button>
                    <button onClick={() => setActiveTab('manual')} className={`px-4 py-2 rounded-full text-xs font-bold uppercase tracking-widest transition-all ${activeTab === 'manual' ? 'bg-white/20 text-white border border-white/50' : 'text-gray-400 hover:text-white'}`}><BookOpen className="w-4 h-4 inline mr-2" />Manual</button>
                </div>

                <div className="relative">
                    <button onClick={() => setIsProfileOpen(!isProfileOpen)} className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 p-[2px] shadow-[0_0_15px_rgba(6,182,212,0.4)]">
                        <div className="w-full h-full bg-[#0a0f1c] rounded-full flex items-center justify-center overflow-hidden">
                            <User className="w-5 h-5 text-cyan-400" />
                        </div>
                    </button>
                    {isProfileOpen && (
                        <div className="absolute right-0 mt-4 w-64 glass-panel rounded-2xl border border-white/10 shadow-[0_20px_50px_rgba(0,0,0,0.8)] overflow-hidden z-50 fade-in-up">
                            <div className="p-5 border-b border-white/10 bg-white/5">
                                <p className="text-sm font-bold text-white uppercase tracking-widest">{user?.name || 'Ayan Sayyad'}</p>
                                <p className="text-[10px] text-cyan-400 font-mono mt-1">{user?.email}</p>
                            </div>
                            <div className="p-2">
                                <button onClick={logout} className="w-full text-left px-4 py-3 text-xs font-bold text-red-400 hover:bg-red-500/20 hover:text-red-300 rounded-xl flex items-center gap-3 uppercase tracking-widest"><LogOut className="w-4 h-4" /> Logout</button>
                            </div>
                        </div>
                    )}
                </div>
            </nav>

            <main className="relative z-10 pt-32 pb-20 px-6 max-w-7xl mx-auto min-h-screen">
                {activeTab === 'repoHealer' && (
                    <div className="fade-in-up">
                        <section className="flex flex-col items-center justify-center min-h-[70vh]">
                            <div className={`relative transition-all duration-700 text-center w-full max-w-5xl mx-auto ${status !== 'IDLE' ? 'opacity-0 -translate-y-20 h-0 overflow-hidden scale-95' : 'opacity-100 translate-y-0 h-auto mb-16'}`}>
                                <h1 className="text-6xl md:text-[6.5rem] font-black tracking-tighter leading-[1.05]">
                                    Just repair it <br/> with <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400">TITAN.</span>
                                </h1>
                            </div>

                            <div className={`relative glass-panel overflow-hidden shadow-[0_30px_80px_rgba(0,0,0,0.8)] mx-auto transition-all duration-1000 ${status === 'IDLE' ? 'w-full max-w-4xl h-[240px] rounded-[2rem] p-4' : 'w-full max-w-5xl h-[550px] rounded-[2rem] p-0 border-blue-500/30'}`}>
                                <div className={`absolute inset-0 w-full h-full transition-opacity duration-500 p-4 ${status === 'IDLE' ? 'opacity-100 z-10' : 'opacity-0 -z-10'}`}>
                                    <form onSubmit={handleRepoHeal} className="flex flex-col h-full gap-3">
                                        <div className="flex flex-col md:flex-row gap-3">
                                            <input type="text" value={repoUrl} onChange={(e) => setRepoUrl(e.target.value)} className="flex-1 bg-black/40 border border-white/10 rounded-2xl px-6 py-4 text-white text-sm outline-none focus:border-blue-500/50" placeholder="Target Repository URL" />
                                            <button type="submit" className="bg-white text-black rounded-2xl px-10 py-4 font-black uppercase tracking-widest text-[10px] shadow-[0_0_20px_rgba(255,255,255,0.2)] hover:bg-gray-200 transition-colors">Deploy Swarm</button>
                                        </div>
                                        <textarea value={crashDesc} onChange={(e) => setCrashDesc(e.target.value)} className="flex-1 bg-black/40 border border-white/10 rounded-2xl px-6 py-4 text-gray-300 font-mono text-sm outline-none focus:border-blue-500/50 resize-none" placeholder="Describe bug or leave empty for full scan..." />
                                    </form>
                                </div>

                                {/* TERMINAL UI WITH MATHS GRID OVERLAY */}
                                <div className={`absolute inset-0 w-full h-full flex flex-col bg-[#050505] transition-opacity duration-700 overflow-hidden ${status !== 'IDLE' ? 'opacity-100 z-10' : 'opacity-0 -z-10'}`}>
                                    
                                    {/* Maths Box Lines & Scanline */}
                                    <div className="absolute inset-0 bg-[linear-gradient(rgba(59,130,246,0.08)_1px,transparent_1px),linear-gradient(90deg,rgba(59,130,246,0.08)_1px,transparent_1px)] bg-[size:30px_30px] pointer-events-none"></div>
                                    <div className="absolute inset-0 bg-gradient-to-b from-transparent via-blue-500/5 to-transparent h-[200%] animate-scanline pointer-events-none"></div>

                                    <div className="relative z-10 flex justify-between items-center border-b border-white/10 p-6 bg-black/60 shrink-0 backdrop-blur-md">
                                        <div className="flex gap-2">
                                            <div className="w-3.5 h-3.5 rounded-full bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.8)]"></div>
                                            <div className="w-3.5 h-3.5 rounded-full bg-yellow-500 shadow-[0_0_10px_rgba(234,179,8,0.8)]"></div>
                                            <div className="w-3.5 h-3.5 rounded-full bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.8)]"></div>
                                        </div>
                                        <div className="text-[10px] text-blue-400/50 font-mono uppercase tracking-widest">SECURE UPLINK ESTABLISHED</div>
                                    </div>
                                    
                                    {status === 'WORKING' ? (
                                        <div className="relative z-10 flex-1 p-8 overflow-y-auto space-y-4 font-mono text-sm">
                                            {terminalLogs.map((log, i) => (<div key={i} className="text-blue-200 flex gap-4 fade-in-up"><ChevronRight className="text-blue-500 w-5 h-5 shrink-0 shadow-[0_0_10px_rgba(59,130,246,0.8)] rounded-full" /> {log}</div>))}
                                        </div>
                                    ) : (
                                        <div className="relative z-10 flex-1 flex flex-col items-center justify-center p-8 text-center bg-[radial-gradient(circle_at_center,rgba(37,99,235,0.1)_0%,transparent_60%)]">
                                            <ShieldAlert className="w-12 h-12 text-blue-400 mb-8 animate-pulse shadow-[0_0_50px_rgba(37,99,235,0.4)] rounded-full bg-blue-500/10 p-2" />
                                            <h2 className="text-4xl font-black mb-4 text-white">Neural Fix Verified.</h2>
                                            <div className="flex gap-6 mt-4">
                                                <button onClick={() => setStatus('IDLE')} className="px-8 py-4 rounded-full border border-white/20 text-xs font-bold uppercase hover:bg-white/5 transition-colors">New Run</button>
                                                <a href={downloadLink} download className="px-8 py-4 rounded-full bg-cyan-500 text-black text-xs font-black uppercase flex items-center gap-3 shadow-[0_0_20px_rgba(6,182,212,0.4)] hover:bg-cyan-400 transition-colors"><Download className="w-4 h-4"/> Extract Payload</a>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </section>

                        <section className="mt-20 pb-10">
                            <div className="max-w-4xl mx-auto glass-panel p-10 rounded-[3rem] scroll-reveal border-purple-500/20 shadow-[0_0_30px_rgba(168,85,247,0.05)]">
                                <h3 className="text-xs font-black text-purple-500 tracking-widest mb-10 text-center uppercase">Real-Time Core Allocation</h3>
                                <div className="space-y-8">
                                    {activeAllocation.map((stat, i) => (
                                        <div key={i}>
                                            <div className="flex justify-between text-xs font-bold uppercase tracking-widest text-gray-400 mb-3">
                                                <span>{stat.label}</span>
                                                <span className="text-white font-mono">{stat.val}</span>
                                            </div>
                                            <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                                                <div className={`h-full ${stat.color} ${stat.shadow} rounded-full transition-all duration-[2s]`} style={{ width: stat.val }}></div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </section>

                        {/* NEW LIQUID GLASS TOOLCHAIN SECTION */}
                        <section className="mt-10 pb-20 scroll-reveal">
                            <div className="max-w-5xl mx-auto glass-panel p-10 rounded-[3rem] border-cyan-500/20 shadow-[0_0_40px_rgba(6,182,212,0.1)] relative overflow-hidden">
                                {/* Liquid Glass Background Blur */}
                                <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-cyan-500/5 backdrop-blur-3xl z-0"></div>
                                
                                <div className="relative z-10">
                                    <h3 className="text-xs font-black text-cyan-400 tracking-widest mb-10 text-center uppercase">TITAN CORE</h3>
                                    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                                        {[
                                            { icon: Code, title: 'Semantic Analysis', desc: 'The AI swarm performs LLM-driven semantic analysis...', color: 'text-blue-400' },
                                            { icon: Layers, title: 'CrewAI Swarm', desc: 'Delegates complex tasks to specialized Python agents.', color: 'text-purple-400' },
                                            { icon: Box, title: 'Sandbox Gen', desc: 'Generates secure, isolated zip packages automatically.', color: 'text-cyan-400' },
                                            { icon: Database, title: 'Audit Ledger', desc: 'Cryptographically logs all auto-remediations to MongoDB.', color: 'text-green-400' }
                                        ].map((tool, idx) => (
                                            <div key={idx} className="bg-black/40 border border-white/5 p-6 rounded-3xl hover:border-cyan-500/30 transition-all duration-300 hover:-translate-y-2 group">
                                                <div className="bg-white/5 w-12 h-12 rounded-2xl flex items-center justify-center mb-4 border border-white/10 group-hover:border-cyan-500/30 transition-colors">
                                                    <tool.icon className={`w-6 h-6 ${tool.color}`} />
                                                </div>
                                                <h4 className="text-white font-bold mb-2">{tool.title}</h4>
                                                <p className="text-[11px] text-gray-500 leading-relaxed">{tool.desc}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </section>

                        <section className="mt-10 pb-20 scroll-reveal">
                            <h3 className="text-xs font-black text-red-500 tracking-widest mb-10 text-center uppercase">Neural Neutralization Matrix</h3>
                            {threatIntel.length === 0 ? (
                                <div className="max-w-4xl mx-auto glass-panel p-10 text-center rounded-3xl border-white/5">
                                    <p className="text-gray-500 uppercase tracking-widest text-xs font-bold">Awaiting neural threats...</p>
                                </div>
                            ) : (
                                <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
                                    {threatIntel.map((intel, idx) => (
                                        <div key={idx} className="glass-panel p-6 rounded-2xl group hover:bg-white/5 transition-colors border-blue-500/20 shadow-[0_10px_30px_rgba(0,0,0,0.5)]">
                                            <div className="flex justify-between items-center mb-4">
                                                <span className="text-xs font-mono text-gray-300 truncate max-w-[150px]">{intel.filePath}</span>
                                                <span className="text-[9px] font-black uppercase tracking-widest px-2 py-1 rounded bg-black/50 text-blue-400 border border-blue-500/20">{intel.status}</span>
                                            </div>
                                            <p className="text-sm font-bold text-white mb-4 line-clamp-2">{intel.issue}</p>
                                            <div className="pt-4 border-t border-white/5 flex justify-between items-center text-[10px] text-gray-500 uppercase tracking-widest">
                                                <span>Diff Impact</span>
                                                <span className="text-cyan-400 font-mono">{intel.charDiff} chars</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </section>
                    </div>
                )}

                {activeTab === 'ledger' && (
                    <section className="fade-in-up min-h-screen pt-10 px-4">
                        <div className="flex justify-between items-end mb-8 max-w-5xl mx-auto">
                            <h2 className="text-4xl font-black text-white">Operations Ledger</h2>
                            <button onClick={fetchTickets} className="text-xs text-gray-400 hover:text-white flex items-center gap-2 font-bold uppercase transition-colors"><Zap className="w-4 h-4" /> Refresh Sync</button>
                        </div>
                        <div className="max-w-5xl mx-auto glass-panel rounded-[3rem] p-8 space-y-4 border-cyan-500/10 shadow-[0_0_40px_rgba(6,182,212,0.05)]">
                            {tickets.length === 0 ? (
                                <div className="text-center py-20 text-gray-500 font-mono uppercase tracking-widest text-sm">No logs detected in core system.</div>
                            ) : (
                                [...tickets].sort((a, b) => new Date(b.createdAt || Date.now()) - new Date(a.createdAt || Date.now())).map((t) => (
                                    <div key={t._id} className={`bg-black/60 border ${t.source === 'Automated' ? 'border-red-500/30 shadow-[0_0_20px_rgba(239,68,68,0.1)]' : 'border-white/5'} p-6 rounded-2xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4 hover:bg-black/80 transition-colors`}>
                                        <div className="flex-1">
                                            <div className="flex items-center flex-wrap gap-3 mb-3">
                                                <span className={`text-[9px] px-3 py-1 rounded-full font-black uppercase tracking-widest border ${t.source === 'Automated' ? 'bg-red-500/10 text-red-400 border-red-500/30' : 'bg-blue-500/10 text-blue-400 border-blue-500/30'}`}>{t.source}</span>
                                                <span className="text-[10px] text-gray-600 font-mono">ID: {t._id.slice(-6)}</span>
                                                <span className="text-[10px] text-cyan-500/80 font-mono border-l border-white/10 pl-3">
                                                    {new Date(t.createdAt).toLocaleString('en-US', { 
                                                        month: 'short', day: 'numeric', 
                                                        hour: '2-digit', minute:'2-digit', second:'2-digit' 
                                                    })}
                                                </span>
                                            </div>
                                            <h4 className="text-lg font-bold text-gray-200">{t.title}</h4>
                                            <p className="text-sm text-gray-500 mt-2 line-clamp-2">{t.description}</p>
                                        </div>
                                        
                                        <div className="flex flex-col md:flex-row items-end md:items-center gap-4">
                                            <div className="flex items-center gap-2 bg-white/5 px-4 py-2 rounded-xl">
                                                <div className={`w-2 h-2 rounded-full ${t.status === 'Resolved' ? 'bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.8)]' : 'bg-yellow-500 shadow-[0_0_10px_rgba(234,179,8,0.8)] animate-pulse'}`}></div>
                                                <span className="text-[10px] text-gray-300 font-bold uppercase tracking-widest">{t.status}</span>
                                            </div>
                                            
                                            <button 
                                                onClick={() => handleDeleteTicket(t._id)}
                                                className="px-4 py-2 rounded-xl border border-red-500/20 text-red-400 text-[10px] font-bold uppercase tracking-widest hover:bg-red-500/10 hover:border-red-500/50 transition-colors"
                                            >
                                                Purge
                                            </button>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </section>
                )}

                {activeTab === 'chaos' && (
                    <section className="flex flex-col items-center justify-center min-h-[70vh] fade-in-up relative z-[9999]">
                        <div className="glass-panel border-red-500/30 rounded-[3rem] p-16 text-center max-w-2xl bg-red-900/10 shadow-[0_0_50px_rgba(220,38,38,0.1)] relative overflow-visible group">
                            <div className="absolute inset-0 bg-red-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none z-0 rounded-[3rem]"></div>
                            
                            <Flame className="relative z-10 w-24 h-24 text-red-500 mx-auto mb-8 animate-pulse drop-shadow-[0_0_15px_rgba(239,68,68,0.8)] pointer-events-none bg-red-500/10 rounded-full p-4" />
                            <h2 className="relative z-10 text-5xl font-black mb-4 text-white pointer-events-none tracking-tight">Chaos Simulator</h2>
                            <p className="relative z-10 text-gray-400 mb-10 text-lg pointer-events-none leading-relaxed">Inject a fatal fault into the backend to verify the Global SRE Trap interceptor and auto-remediation logs.</p>
                            
                            <button 
                                type="button"
                                onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    triggerChaosMonkey();
                                }} 
                                className="relative z-[9999] pointer-events-auto px-10 py-5 bg-red-600 hover:bg-red-500 text-white font-black uppercase tracking-widest rounded-full transition-all shadow-[0_0_30px_rgba(220,38,38,0.4)] hover:shadow-[0_0_50px_rgba(220,38,38,0.6)] cursor-pointer active:scale-95"
                            >
                                Inject Chaos Payload
                            </button>
                        </div>
                    </section>
                )}

                {/* -------- UPDATED ENHANCED MANUAL SECTION -------- */}
                {activeTab === 'manual' && (
                    <section className="max-w-5xl mx-auto fade-in-up pt-10 pb-20 min-h-screen">
                        <div className="flex flex-col items-center text-center mb-16">
                            <BookOpen className="w-16 h-16 text-blue-400 mb-6 shadow-[0_0_30px_rgba(96,165,250,0.2)] rounded-full bg-blue-500/10 p-3" />
                            <h2 className="text-5xl font-black text-white mb-4 tracking-tight">System Documentation</h2>
                            <p className="text-gray-400 max-w-2xl text-lg leading-relaxed">Complete architectural breakdown of the TITAN Neural Core and its automated DevSecOps remediation subsystems.</p>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            {/* Card 1 */}
                            <div className="glass-panel rounded-[3rem] p-10 hover:border-blue-500/30 transition-all duration-300 shadow-[0_0_30px_rgba(0,0,0,0.5)] group hover:-translate-y-2">
                                <div className="w-16 h-16 rounded-2xl bg-blue-500/10 flex items-center justify-center mb-6 border border-blue-500/20 group-hover:bg-blue-500/20 transition-colors">
                                    <Activity className="w-8 h-8 text-blue-400" />
                                </div>
                                <h3 className="text-2xl font-black text-white mb-4">Autonomous Diagnostics</h3>
                                <p className="text-gray-400 leading-relaxed text-sm"><p className="text-gray-400 leading-relaxed text-sm">Input a target GitHub URL and crash logs. The AI swarm performs semantic code analysis, generates a logic patch, and packages the remediated repository into a deployable ZIP payload.</p></p>
                            </div>
                            
                            {/* Card 2 */}
                            <div className="glass-panel rounded-[3rem] p-10 hover:border-red-500/30 transition-all duration-300 shadow-[0_0_30px_rgba(0,0,0,0.5)] group hover:-translate-y-2">
                                <div className="w-16 h-16 rounded-2xl bg-red-500/10 flex items-center justify-center mb-6 border border-red-500/20 group-hover:bg-red-500/20 transition-colors">
                                    <Flame className="w-8 h-8 text-red-400" />
                                </div>
                                <h3 className="text-2xl font-black text-white mb-4">Chaos Testing</h3>
                                <p className="text-gray-400 leading-relaxed text-sm">Validate the SRE trap by triggering deliberate server faults. Intercepted crashes are logged instantly to the database and displayed in the immutable Ledger for engineer review.</p>
                            </div>
                            
                            {/* Card 3 */}
                            <div className="glass-panel rounded-[3rem] p-10 hover:border-purple-500/30 transition-all duration-300 shadow-[0_0_30px_rgba(0,0,0,0.5)] group hover:-translate-y-2">
                                <div className="w-16 h-16 rounded-2xl bg-purple-500/10 flex items-center justify-center mb-6 border border-purple-500/20 group-hover:bg-purple-500/20 transition-colors">
                                    <Layers className="w-8 h-8 text-purple-400" />
                                </div>
                                <h3 className="text-2xl font-black text-white mb-4">LLM Swarm Engine</h3>
                                <p className="text-gray-400 leading-relaxed text-sm">Powered by LiteLLM and CrewAI, the agentic swarm divides labor between Chief Architects, Security Auditors, and Code Fixers to ensure robust, production-ready code patches.</p>
                            </div>
                            
                            {/* Card 4 */}
                            <div className="glass-panel rounded-[3rem] p-10 hover:border-green-500/30 transition-all duration-300 shadow-[0_0_30px_rgba(0,0,0,0.5)] group hover:-translate-y-2">
                                <div className="w-16 h-16 rounded-2xl bg-green-500/10 flex items-center justify-center mb-6 border border-green-500/20 group-hover:bg-green-500/20 transition-colors">
                                    <ShieldCheck className="w-8 h-8 text-green-400" />
                                </div>
                                <h3 className="text-2xl font-black text-white mb-4">Global Middleware Trap</h3>
                                <p className="text-gray-400 leading-relaxed text-sm">An Express.js global error handler that catches unhandled promise rejections and fatal runtime errors, freezing the crash state and alerting the assigned SRE via Email.</p>
                            </div>
                        </div>
                    </section>
                )}
            </main>

            <footer className="relative z-10 border-t border-white/5 py-12 text-center bg-black/40 backdrop-blur-sm">
                <p className="text-gray-500 text-[10px] uppercase tracking-[0.4em] font-black">
                    TITAN Autonomous SRE Engine © 2026. <br/>
                    <span className="mt-2 inline-block text-gray-600 font-mono tracking-normal">Built for SPPU Internship Defense</span>
                </p>
            </footer>
        </div>
    );
};

export default Dashboard;