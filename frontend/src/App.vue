<script setup lang="ts">
import { ref } from "vue";
import { RouterView, RouterLink, useRouter } from "vue-router";
import { useI18n } from "./composables/useI18n";
import { useMessages } from "./composables/useMessages";
import Toast from "typescript-toastify";

const router = useRouter();
const { fetchMessages } = useMessages();

router.afterEach(async () => {
  const messages = await fetchMessages();

  for (const [level, msg] of messages) {
    new Toast({
      position: "top-right",
      toastMsg: msg,
      type: level === "error" ? "error" : "success",
      autoCloseTime: 1000000,
    });
  }
});
const { t, locale, setLocale } = useI18n();
const isMenuOpen = ref(false);

const toggleMenu = () => {
  isMenuOpen.value = !isMenuOpen.value;
};

const closeMenu = () => {
  isMenuOpen.value = false;
};
</script>

<template>
  <div>
    <nav class="navbar">
      <div class="container navbar-content">
        <RouterLink
          to="/"
          class="navbar-brand"
          @click="closeMenu"
          aria-label="Home"
        >
          <img src="/logo.png" alt="Logo" class="navbar-logo" />
          <span class="navbar-app-name">{{ t("nav.app_name") }}</span>
        </RouterLink>

        <!-- Hamburger Button -->
        <button
          class="menu-toggle"
          :class="{ active: isMenuOpen }"
          @click="toggleMenu"
          aria-label="Toggle Navigation"
        >
          <span class="hamburger-line"></span>
          <span class="hamburger-line"></span>
          <span class="hamburger-line"></span>
        </button>

        <div class="nav-container" :class="{ 'menu-open': isMenuOpen }">
          <div class="nav-links">
            <RouterLink to="/" class="nav-link" @click="closeMenu">
              🏕️ {{ t("nav.camps") }}</RouterLink
            >
            <RouterLink to="/recipes" class="nav-link" @click="closeMenu">
              🥘 {{ t("nav.recipes") }}</RouterLink
            >
            <RouterLink
              to="/account"
              class="nav-link"
              aria-label="Account Settings"
              @click="closeMenu"
              >👤 {{ t("nav.account") }}</RouterLink
            >
          </div>

          <div class="lang-switcher">
            <button
              id="lang-de"
              class="lang-btn"
              :class="{ active: locale === 'de' }"
              @click="setLocale('de')"
              title="Deutsch"
            >
              🇩🇪
            </button>
            <button
              id="lang-fr"
              class="lang-btn"
              :class="{ active: locale === 'fr' }"
              @click="setLocale('fr')"
              title="Français"
            >
              🇫🇷
            </button>
          </div>
        </div>
      </div>
    </nav>
    <main class="container page-container">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.navbar-brand {
  margin: 0;
  font-size: 1.4rem;
  color: var(--color-primary);
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 800;
  text-decoration: none;
  transition: opacity 0.2s;
}

.navbar-brand:hover {
  opacity: 0.9;
}

.navbar-logo {
  width: 3.8rem;
  height: 3.8rem;
  object-fit: contain;
  filter: drop-shadow(0 2px 4px rgba(16, 185, 129, 0.2));
  transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.navbar-brand:hover .navbar-logo {
  transform: scale(1.15);
}

.navbar-app-name {
  background: linear-gradient(
    135deg,
    var(--color-primary),
    var(--color-primary-hover)
  );
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -0.02em;
}

.nav-container {
  display: flex;
  gap: 1.5rem;
  align-items: center;
}

.nav-links {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.menu-toggle {
  display: none;
  flex-direction: column;
  justify-content: space-around;
  width: 2rem;
  height: 2rem;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 5px;
  z-index: 100;
}

.hamburger-line {
  width: 1.5rem;
  height: 2px;
  background: var(--color-text-main);
  border-radius: 10px;
  transition: all 0.3s linear;
  position: relative;
  transform-origin: 1px;
}

.lang-switcher {
  display: flex;
  gap: 0.25rem;
  align-items: center;
}

.lang-btn {
  background: none;
  border: 2px solid transparent;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1.1rem;
  padding: 2px 4px;
  line-height: 1;
  opacity: 0.5;
  transition:
    opacity 0.15s,
    border-color 0.15s;
}

.lang-btn:hover {
  opacity: 0.9;
}

.lang-btn.active {
  opacity: 1;
  border-color: var(--color-primary);
}

/* Mobile responsive styles */
@media (max-width: 768px) {
  .menu-toggle {
    display: flex;
  }

  /* Hamburger animations */
  .menu-toggle.active .hamburger-line:nth-child(1) {
    transform: rotate(45deg);
  }

  .menu-toggle.active .hamburger-line:nth-child(2) {
    opacity: 0;
    transform: translateX(20px);
  }

  .menu-toggle.active .hamburger-line:nth-child(3) {
    transform: rotate(-45deg);
  }

  .nav-container {
    position: fixed;
    top: 4rem;
    left: 0;
    width: 100%;
    height: 0;
    background: var(--color-bg-surface);
    flex-direction: column;
    overflow: hidden;
    transition:
      height 0.3s ease-in-out,
      box-shadow 0.3s ease;
    z-index: 40;
    padding: 0;
    gap: 0;
  }

  .nav-container.menu-open {
    height: auto;
    padding-bottom: 2rem;
    box-shadow: var(--shadow-lg);
    border-bottom: 1px solid var(--color-border);
  }

  .nav-links {
    flex-direction: column;
    width: 100%;
    padding: 1rem 0;
    gap: 0;
  }

  .nav-link {
    width: 100%;
    text-align: center;
    padding: 1rem;
    border-radius: 0;
    border-bottom: 1px solid var(--color-bg-mute);
  }

  .lang-switcher {
    padding: 1rem;
    justify-content: center;
    width: 100%;
  }

  .navbar-content {
    justify-content: space-between;
  }
}
</style>
