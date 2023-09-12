export async function fetchAuthorsList(offset = 0, limit = 100) {
    let url = "http://127.0.0.1:8000/authors/";
    try {
        let response = await fetch(url);
        if (!response.ok) {
            throw `http status code ${response.status}`;
        }
        let data = await response.json();
        return {success: true, data};
    }
    catch (error) {
        console.error(`Failed to fetch ${url}:`, error);
    }
    return {success: false};
}