import React, { useState, useContext } from 'react';
import { Link } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { ShieldAlert } from 'lucide-react';

const Register = () => {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const { login } = useContext(AuthContext);

    const handleRegister = async (e) => {
        e.preventDefault();
        setError('');
        try {
            const res = await fetch('https://project-titan-ychw.onrender.com/api/users', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, password }),
            });
            const data = await res.json();
            if (res.ok) {
                login(data);
            } else {
                setError(data.message || 'Registration sequence failed.');
            }
        } catch (err) {
            setError('Connection Error: Backend unreachable.');
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-[#020202] via-[#0a1c12] to-[#020202] relative overflow-hidden">
            
            {/* Background Orbs */}
            <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-green-600/10 rounded-full blur-[100px] pointer-events-none"></div>

            {/* Liquid Glass Card */}
            <div className="bg-white/5 backdrop-blur-xl border border-white/10 p-10 rounded-[2rem] shadow-[0_8px_32px_0_rgba(0,0,0,0.5)] w-full max-w-md relative z-10">
                
                <div className="flex flex-col items-center mb-8">
                    <h1 className="text-2xl font-bold text-center text-white tracking-widest">ENLIST <span className="text-green-400">ENGINEER</span></h1>
                    <p className="text-xs text-gray-400 mt-2 uppercase tracking-widest">System Registration</p>
                </div>
                
                {error && (
                    <div className="mb-6 p-3 bg-red-900/30 border border-red-500/50 backdrop-blur-md rounded-xl flex items-center gap-3 text-red-400 text-sm">
                        <ShieldAlert className="w-5 h-5 shrink-0" /> {error}
                    </div>
                )}
                
                <form onSubmit={handleRegister} className="space-y-5">
                    <div>
                        <label className="block text-xs uppercase tracking-widest text-gray-400 mb-2 ml-1">Full Name</label>
                        <input type="text" required className="w-full bg-black/40 border border-white/10 text-white rounded-xl p-4 outline-none focus:border-green-500/50 focus:bg-black/60 transition-all" value={name} onChange={(e) => setName(e.target.value)} />
                    </div>
                    <div>
                        <label className="block text-xs uppercase tracking-widest text-gray-400 mb-2 ml-1">Work Email</label>
                        <input type="email" required className="w-full bg-black/40 border border-white/10 text-white rounded-xl p-4 outline-none focus:border-green-500/50 focus:bg-black/60 transition-all" value={email} onChange={(e) => setEmail(e.target.value)} />
                    </div>
                    <div>
                        <label className="block text-xs uppercase tracking-widest text-gray-400 mb-2 ml-1">Set Password</label>
                        <input type="password" required className="w-full bg-black/40 border border-white/10 text-white rounded-xl p-4 outline-none focus:border-green-500/50 focus:bg-black/60 transition-all" value={password} onChange={(e) => setPassword(e.target.value)} />
                    </div>
                    <button type="submit" className="w-full py-4 mt-4 rounded-xl font-bold uppercase tracking-widest bg-green-500 hover:bg-green-400 text-black transition-all shadow-[0_0_20px_rgba(34,197,94,0.2)] hover:shadow-[0_0_30px_rgba(34,197,94,0.4)]">
                        Initialize Access
                    </button>
                </form>

                <p className="text-center text-sm text-gray-400 mt-8 border-t border-white/10 pt-6">
                    Already cleared? <Link to="/" className="text-green-400 hover:text-green-300 font-bold tracking-wide ml-1 transition-colors">Login here</Link>
                </p>
            </div>
        </div>
    );
};

export default Register;