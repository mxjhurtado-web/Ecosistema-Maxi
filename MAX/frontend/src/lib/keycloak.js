/**
 * Keycloak configuration for MAX frontend
 */
import Keycloak from 'keycloak-js';

const keycloakConfig = {
    url: import.meta.env.VITE_KEYCLOAK_URL || 'http://localhost:8081',
    realm: import.meta.env.VITE_KEYCLOAK_REALM || 'maxibot',
    clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'maxibot-client',
};

const keycloak = new Keycloak(keycloakConfig);

export default keycloak;
