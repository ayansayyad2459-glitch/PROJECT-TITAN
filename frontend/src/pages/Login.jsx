import React, { useState, useContext } from 'react';
import { Link } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { Terminal, ShieldAlert } from 'lucide-react';

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const { login } = useContext(AuthContext);

    const handleLogin = async (e) => {
        e.preventDefault();
        setError('');
        try {
            const res = await fetch('http://localhost:5000/api/users/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            });
            const data = await res.json();
            
            if (res.ok) {
                login(data);
            } else {
                setError(data.message || 'Access Denied: Invalid Credentials');
            }
        } catch (err) {
            setError('Backend Offline: Ensure node server.js is running.');
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-[#020202] via-[#0a0f1c] to-[#020202] relative overflow-hidden">
            
            {/* Background Orbs */}
            <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-600/20 rounded-full blur-[100px] pointer-events-none"></div>
            <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-600/20 rounded-full blur-[100px] pointer-events-none"></div>

            {/* Liquid Glass Card */}
            <div className="bg-white/5 backdrop-blur-xl border border-white/10 p-10 rounded-[2rem] shadow-[0_8px_32px_0_rgba(0,0,0,0.5)] w-full max-w-md relative z-10">
                <div className="flex flex-col items-center mb-8">
                    <div className="bg-white/10 p-4 rounded-full border border-white/5 mb-4 shadow-[inset_0_0_20px_rgba(255,255,255,0.05)]">
                        <Terminal className="text-cyan-400 w-10 h-10" />
                    </div>
                    <h1 className="text-3xl font-bold tracking-widest text-white">TITAN <span className="text-cyan-400">LOGIN</span></h1>
                    <p className="text-xs text-gray-400 mt-2 uppercase tracking-widest">SRE Command Access</p>
                </div>

                {error && (
                    <div className="mb-6 p-3 bg-red-900/30 border border-red-500/50 backdrop-blur-md rounded-xl flex items-center gap-3 text-red-400 text-sm">
                        <ShieldAlert className="w-5 h-5 shrink-0" /> {error}
                    </div>
                )}

                <form onSubmit={handleLogin} className="space-y-6">
                    <div>
                        <label className="block text-xs uppercase tracking-widest text-gray-400 mb-2 ml-1">Engineer Email</label>
                        <input type="email" required className="w-full bg-black/40 border border-white/10 text-white rounded-xl p-4 outline-none focus:border-cyan-500/50 focus:bg-black/60 transition-all placeholder-gray-600" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="operator@titan.core" />
                    </div>
                    <div>
                        <label className="block text-xs uppercase tracking-widest text-gray-400 mb-2 ml-1">Access Key</label>
                        <input type="password" required className="w-full bg-black/40 border border-white/10 text-white rounded-xl p-4 outline-none focus:border-cyan-500/50 focus:bg-black/60 transition-all" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
                    </div>
                    <button type="submit" className="w-full py-4 mt-2 rounded-xl font-bold uppercase tracking-widest bg-cyan-500 hover:bg-cyan-400 text-black transition-all shadow-[0_0_20px_rgba(6,182,212,0.3)] hover:shadow-[0_0_30px_rgba(6,182,212,0.5)]">
                        Authorize Session
                    </button>
                </form>

                <p className="text-center text-sm text-gray-400 mt-8 border-t border-white/10 pt-6">
                    New Engineer? <Link to="/register" className="text-cyan-400 hover:text-cyan-300 font-bold tracking-wide ml-1 transition-colors">Register Clearance</Link>
                </p>
            </div>
        </div>
    );
};

export default Login;