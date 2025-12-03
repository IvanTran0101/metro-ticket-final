import { client } from './client';

export async function login(credentials) {
    const res = await client.post('/auth/login', {
        username: credentials.username,
        password: credentials.password
    });

    if (res.access_token) {
        localStorage.setItem('access_token', res.access_token);
    }
    return res;
}

export async function getMe() {
    return client.get('/account/me');
}
