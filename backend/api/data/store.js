/**
 * In-memory data store
 */

import { v4 as uuidv4 } from 'uuid';

// ============================================================================
// Data
// ============================================================================

const users = [];
const sessions = [];
const lessons = [
    { id: 'l1', title: 'Aleph-Bet Basics', description: 'Learn the first 5 letters.', difficulty: 'beginner', duration: 10, xpReward: 50, content: [] },
    { id: 'l2', title: 'Simple Greetings', description: 'Say hello and goodbye.', difficulty: 'beginner', duration: 15, xpReward: 60, content: [] },
];
const quizzes = [
    { id: 'q1', lessonId: 'l1', title: 'Aleph-Bet Quiz', questions: [{text: 'Q1'}, {text: 'Q2'}, {text: 'Q3'}] },
    { id: 'q2', lessonId: 'l2', title: 'Greetings Quiz', questions: [] },
];
const dictionary = [
    { id: 'd1', hebrew: 'שָׁלוֹם', english: 'Hello / Peace', pronunciation: 'shalom' },
    { id: 'd2', hebrew: 'תּוֹדָה', english: 'Thank you', pronunciation: 'toda' },
];
const quizAttempts = [];

// ============================================================================
// Store Implementation
// ============================================================================

const store = {
    // ========================================================================
    // User Functions
    // ========================================================================

    createUser: (userData) => {
        const newUser = {
            id: uuidv4(),
            ...userData,
            xpTotal: 0,
            level: 1,
            lessonsCompleted: [],
            quizzesCompleted: [],
            streak: 0,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
        };
        users.push(newUser);
        return newUser;
    },

    getUserByEmail: (email) => {
        return users.find(user => user.email === email);
    },

    getUserById: (userId) => {
        return users.find(user => user.id === userId);
    },

    getAllUsers: () => {
        return users;
    },

    updateUser: (userId, updates) => {
        const user = users.find(u => u.id === userId);
        if (user) {
            Object.assign(user, updates);
            user.updatedAt = new Date().toISOString();
            return user;
        }
        return null;
    },

    // ========================================================================
    // Session Functions
    // ========================================================================

    createSession: (userId) => {
        const newSession = {
            token: uuidv4(),
            userId,
            createdAt: new Date().toISOString(),
            expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // 24 hours
        };
        sessions.push(newSession);
        return newSession;
    },

    getSession: (token) => {
        return sessions.find(session => session.token === token);
    },

    deleteSession: (token) => {
        const index = sessions.findIndex(session => session.token === token);
        if (index !== -1) {
            sessions.splice(index, 1);
        }
    },

    // ========================================================================
    // Lesson Functions
    // ========================================================================

    getAllLessons: () => lessons,
    getLessonById: (id) => lessons.find(l => l.id === id),
    createLesson: (data) => {
        const newLesson = { id: uuidv4(), ...data };
        lessons.push(newLesson);
        return newLesson;
    },
    updateLesson: (id, updates) => {
        const lesson = lessons.find(l => l.id === id);
        if (lesson) {
            Object.assign(lesson, updates);
            return lesson;
        }
        return null;
    },
    completeLesson: (userId, lessonId) => {
        const user = store.getUserById(userId);
        const lesson = store.getLessonById(lessonId);
        if (user && lesson && !user.lessonsCompleted.includes(lessonId)) {
            user.lessonsCompleted.push(lessonId);
            user.xpTotal += lesson.xpReward || 50;
            // Simple level up logic
            if (user.xpTotal >= user.level * 100) {
                user.level++;
            }
            return user;
        }
        return user;
    },

    // ========================================================================
    // Quiz Functions
    // ========================================================================

    getAllQuizzes: () => quizzes,
    getQuizById: (id) => quizzes.find(q => q.id === id),
    createQuiz: (data) => {
        const newQuiz = { id: uuidv4(), ...data };
        quizzes.push(newQuiz);
        return newQuiz;
    },
    submitQuizAttempt: (userId, quizId, answers) => {
        const attempt = {
            id: uuidv4(),
            userId,
            quizId,
            answers,
            score: 100,
            passed: true,
            completedAt: new Date().toISOString(),
        };
        quizAttempts.push(attempt);
        const user = store.getUserById(userId);
        if(user && !user.quizzesCompleted.includes(quizId)) {
            user.quizzesCompleted.push(quizId);
        }
        return attempt;
    },
    getQuizAttempts: (userId, quizId) => {
        return quizAttempts.filter(a => a.userId === userId && a.quizId === quizId);
    },

    // ========================================================================
    // Dictionary Functions
    // ========================================================================

    getAllDictionaryWords: () => dictionary,
    getDictionaryWordById: (id) => dictionary.find(w => w.id === id),
    searchDictionary: (query) => {
        const lowerQuery = query.toLowerCase();
        return dictionary.filter(w =>
            w.english.toLowerCase().includes(lowerQuery) ||
            w.hebrew.toLowerCase().includes(lowerQuery) ||
            w.pronunciation.toLowerCase().includes(lowerQuery)
        );
    },
    addDictionaryWord: (data) => {
        const newWord = { id: uuidv4(), ...data };
        dictionary.push(newWord);
        return newWord;
    },


    // ========================================================================
    // Progress Functions
    // ========================================================================

    getUserProgress: (userId) => {
        const user = store.getUserById(userId);
        if (!user) return null;
        return {
            userId,
            xpTotal: user.xpTotal,
            level: user.level,
            lessonsCompleted: user.lessonsCompleted,
            quizzesCompleted: user.quizzesCompleted,
            lastActiveDate: user.updatedAt,
        };
    },

    // ========================================================================
    // Debugging
    // ========================================================================

    _getUsers: () => users,
    _getSessions: () => sessions,
    _clear: () => {
        users.length = 0;
        sessions.length = 0;
    }
};

export { store };