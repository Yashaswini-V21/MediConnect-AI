import { initializeApp } from 'firebase/app';
import {
  getAuth,
  onAuthStateChanged,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut as firebaseSignOut,
  updateProfile
} from 'firebase/auth';

const cleanEnv = (value) => (value || '').trim();

const firebaseConfig = {
  apiKey: cleanEnv(process.env.REACT_APP_FIREBASE_API_KEY),
  authDomain: cleanEnv(process.env.REACT_APP_FIREBASE_AUTH_DOMAIN),
  projectId: cleanEnv(process.env.REACT_APP_FIREBASE_PROJECT_ID),
  appId: cleanEnv(process.env.REACT_APP_FIREBASE_APP_ID)
};

const missingConfig = Object.entries(firebaseConfig)
  .filter(([, value]) => !value)
  .map(([key]) => key);

if (missingConfig.length > 0) {
  throw new Error(`Missing Firebase environment variables: ${missingConfig.join(', ')}`);
}

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);

const mapFirebaseError = (error) => {
  if (!error?.code) return error;

  const errorMessages = {
    'auth/email-already-in-use': 'This email is already in use.',
    'auth/invalid-email': 'Invalid email address.',
    'auth/weak-password': 'Password should be at least 6 characters.',
    'auth/operation-not-allowed': 'Email/Password sign-in is not enabled in Firebase Auth.',
    'auth/admin-restricted-operation': 'This operation is blocked by Firebase project settings.',
    'auth/network-request-failed': 'Network error while contacting Firebase. Check internet and try again.',
    'auth/invalid-api-key': 'Invalid Firebase API key. Verify REACT_APP_FIREBASE_API_KEY.',
    'auth/app-not-authorized': 'Current domain is not authorized in Firebase Authentication settings.',
    'auth/invalid-credential': 'Invalid email or password.',
    'auth/user-not-found': 'User not found.',
    'auth/wrong-password': 'Invalid email or password.',
    'auth/too-many-requests': 'Too many attempts. Please try again later.'
  };

  return {
    ...error,
    message: errorMessages[error.code] || error.message
  };
};

// Keep the same helper contract so existing components need minimal changes.
export const authHelpers = {
  signUp: async (email, password, fullName) => {
    try {
      const credential = await createUserWithEmailAndPassword(auth, email, password);
      if (fullName) {
        await updateProfile(credential.user, { displayName: fullName });
      }

      return {
        data: {
          user: credential.user,
          session: { user: credential.user }
        },
        error: null
      };
    } catch (error) {
      return { data: null, error: mapFirebaseError(error) };
    }
  },

  signIn: async (email, password) => {
    try {
      const credential = await signInWithEmailAndPassword(auth, email, password);
      return {
        data: {
          user: credential.user,
          session: { user: credential.user }
        },
        error: null
      };
    } catch (error) {
      return { data: null, error: mapFirebaseError(error) };
    }
  },

  signOut: async () => {
    try {
      await firebaseSignOut(auth);
      return { error: null };
    } catch (error) {
      return { error: mapFirebaseError(error) };
    }
  },

  getCurrentUser: async () => ({ user: auth.currentUser, error: null }),

  getSession: async () => ({
    session: auth.currentUser ? { user: auth.currentUser } : null,
    error: null
  }),

  getIdToken: async () => {
    if (!auth.currentUser) return null;
    return auth.currentUser.getIdToken();
  },

  onAuthStateChange: (callback) => {
    let previousUser = auth.currentUser;

    const unsubscribe = onAuthStateChanged(auth, (user) => {
      const event = user && !previousUser
        ? 'SIGNED_IN'
        : !user && previousUser
          ? 'SIGNED_OUT'
          : 'TOKEN_REFRESHED';

      previousUser = user;
      callback(event, user ? { user } : null);
    });

    return {
      data: {
        subscription: {
          unsubscribe
        }
      }
    };
  }
};

export default auth;
