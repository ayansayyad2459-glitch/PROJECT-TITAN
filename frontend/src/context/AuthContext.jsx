import React, { createContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        const userInfo = localStorage.getItem('titanUser');
        if (userInfo) {
            setUser(JSON.parse(userInfo));
        }
    }, []);

    const login = (userData) => {
        localStorage.setItem('titanUser', JSON.stringify(userData));
        setUser(userData);
        navigate('/dashboard');
    };

    const logout = () => {
        localStorage.removeItem('titanUser');
        setUser(null);
        navigate('/'); 
    };

    return (
        <AuthContext.Provider value={{ user, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
};