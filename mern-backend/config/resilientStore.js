const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const dataDir = path.resolve(__dirname, '../data');
const dbFile = path.join(dataDir, 'titan_local_store.json');

// Ensure data folder exists
if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
}

// Ensure database file exists
if (!fs.existsSync(dbFile)) {
    fs.writeFileSync(dbFile, JSON.stringify({ users: [], tickets: [] }, null, 2), 'utf-8');
}

const readStore = () => {
    try {
        const raw = fs.readFileSync(dbFile, 'utf-8');
        return JSON.parse(raw);
    } catch (e) {
        return { users: [], tickets: [] };
    }
};

const writeStore = (data) => {
    try {
        fs.writeFileSync(dbFile, JSON.stringify(data, null, 2), 'utf-8');
    } catch (e) {
        console.error('[TITAN STORE] Write error:', e.message);
    }
};

const generateObjectId = () => {
    return crypto.randomBytes(12).toString('hex');
};

// --- QUERY CHAIN WRAPPER ---
class QueryChain {
    constructor(dataPromise) {
        this.promise = Promise.resolve(dataPromise);
    }

    select(fields) {
        return new QueryChain(this.promise.then(result => {
            if (!result) return result;
            const excludePassword = fields && fields.includes('-password');
            if (Array.isArray(result)) {
                return result.map(item => {
                    const copy = { ...item };
                    if (excludePassword) delete copy.password;
                    return copy;
                });
            } else {
                const copy = { ...result };
                if (excludePassword) delete copy.password;
                return copy;
            }
        }));
    }

    sort(sortSpec) {
        return new QueryChain(this.promise.then(result => {
            if (!Array.isArray(result)) return result;
            return [...result].sort((a, b) => {
                // Default descending by createdAt
                const dateA = new Date(a.createdAt || 0).getTime();
                const dateB = new Date(b.createdAt || 0).getTime();
                return dateB - dateA;
            });
        }));
    }

    limit(num) {
        return new QueryChain(this.promise.then(result => {
            if (!Array.isArray(result)) return result;
            return result.slice(0, num);
        }));
    }

    then(onFulfilled, onRejected) {
        return this.promise.then(onFulfilled, onRejected);
    }

    catch(onRejected) {
        return this.promise.catch(onRejected);
    }
}

// --- RESILIENT USER ADAPTER ---
const ResilientUser = {
    async findOne(query) {
        const store = readStore();
        let user = null;
        if (query.email) {
            user = store.users.find(u => u.email.toLowerCase() === query.email.toLowerCase());
        } else if (query._id) {
            user = store.users.find(u => u._id === query._id.toString() || u.id === query._id.toString());
        }
        return user ? { ...user } : null;
    },

    async create(doc) {
        const store = readStore();
        const _id = generateObjectId();
        const now = new Date().toISOString();
        const newUser = {
            _id: _id,
            id: _id,
            name: doc.name || 'Engineer',
            email: doc.email,
            password: doc.password,
            isAdmin: doc.isAdmin || false,
            encryptedKey: doc.encryptedKey || null,
            hasValidKey: doc.hasValidKey || false,
            createdAt: now,
            updatedAt: now
        };
        store.users.push(newUser);
        writeStore(store);
        return { ...newUser };
    },

    findById(id) {
        const queryPromise = (async () => {
            if (!id) return null;
            const targetId = id._id ? id._id.toString() : id.toString();
            const store = readStore();
            const user = store.users.find(u => u._id === targetId || u.id === targetId);
            return user ? { ...user } : null;
        })();
        return new QueryChain(queryPromise);
    },

    find(query = {}) {
        const queryPromise = (async () => {
            const store = readStore();
            return store.users.map(u => ({ ...u }));
        })();
        return new QueryChain(queryPromise);
    },

    async findByIdAndUpdate(id, update, options = {}) {
        const targetId = id._id ? id._id.toString() : id.toString();
        const store = readStore();
        const idx = store.users.findIndex(u => u._id === targetId || u.id === targetId);
        if (idx === -1) return null;

        const updated = {
            ...store.users[idx],
            ...update,
            updatedAt: new Date().toISOString()
        };
        store.users[idx] = updated;
        writeStore(store);
        return { ...updated };
    }
};

// --- RESILIENT TICKET ADAPTER ---
const ResilientTicket = {
    async create(doc) {
        const store = readStore();
        const _id = generateObjectId();
        const now = new Date().toISOString();
        const newTicket = {
            _id: _id,
            id: _id,
            title: doc.title || 'Operational Incident',
            description: doc.description || 'Automated Incident Log',
            user: doc.user ? doc.user.toString() : null,
            source: doc.source || 'Manual',
            status: doc.status || 'Open',
            charDiff: doc.charDiff || (Math.floor(Math.random() * 200) - 100),
            createdAt: now,
            updatedAt: now
        };
        store.tickets.unshift(newTicket);
        writeStore(store);
        return { ...newTicket };
    },

    find(query = {}) {
        const queryPromise = (async () => {
            const store = readStore();
            let results = store.tickets;
            if (query.user) {
                const uid = query.user.toString();
                results = results.filter(t => t.user === uid);
            }
            if (query.status) {
                results = results.filter(t => t.status === query.status);
            }
            return results.map(t => ({ ...t }));
        })();
        return new QueryChain(queryPromise);
    },

    async findById(id) {
        if (!id) return null;
        const targetId = id.toString();
        const store = readStore();
        const ticket = store.tickets.find(t => t._id === targetId || t.id === targetId);
        return ticket ? { ...ticket } : null;
    },

    async findByIdAndUpdate(id, update, options = {}) {
        const targetId = id.toString();
        const store = readStore();
        const idx = store.tickets.findIndex(t => t._id === targetId || t.id === targetId);
        if (idx === -1) return null;

        const updated = {
            ...store.tickets[idx],
            ...update,
            updatedAt: new Date().toISOString()
        };
        store.tickets[idx] = updated;
        writeStore(store);
        return { ...updated };
    },

    async findByIdAndDelete(id) {
        const targetId = id.toString();
        const store = readStore();
        const idx = store.tickets.findIndex(t => t._id === targetId || t.id === targetId);
        if (idx === -1) return null;

        const deleted = store.tickets.splice(idx, 1)[0];
        writeStore(store);
        return { ...deleted };
    }
};

module.exports = { ResilientUser, ResilientTicket };
