importScripts('https://www.gstatic.com/firebasejs/10.0.0/firebase-app-compat.js')
importScripts('https://www.gstatic.com/firebasejs/10.0.0/firebase-messaging-compat.js')

// 빌드 시 실제 값으로 교체 필요
const firebaseConfig = {
  apiKey: "VITE_FIREBASE_API_KEY_VALUE",
  projectId: "VITE_FIREBASE_PROJECT_ID_VALUE",
  messagingSenderId: "VITE_FIREBASE_MESSAGING_SENDER_ID_VALUE",
  appId: "VITE_FIREBASE_APP_ID_VALUE",
}

firebase.initializeApp(firebaseConfig)
const messaging = firebase.messaging()

messaging.onBackgroundMessage((payload) => {
  self.registration.showNotification(payload.notification.title, {
    body: payload.notification.body,
    icon: '/favicon.ico',
  })
})