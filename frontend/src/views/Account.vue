<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useI18n } from "../composables/useI18n";

const { t } = useI18n();
const router = useRouter();

const account = ref<any>(null);
const first_name = ref("");
const last_name = ref("");
const old_password = ref("");
const new_password = ref("");
const confirm_password = ref("");

const loading = ref(true);
const profileMsg = ref({ type: "", text: "" });
const passwordMsg = ref({ type: "", text: "" });

async function fetchAccount() {
  try {
    const res = await fetch("/api/auth/account");
    if (res.ok) {
      const data = await res.json();
      if (!data.username) {
        router.push("/login");
        return;
      }
      account.value = data;
      first_name.value = account.value.first_name || "";
      last_name.value = account.value.last_name || "";
    } else {
      router.push("/login");
    }
  } catch (err) {
    console.error(err);
  } finally {
    loading.value = false;
  }
}

function getCookie(name: string) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function getCsrfToken() {
  return (
    getCookie("csrftoken") ||
    (document.querySelector("[name=csrfmiddlewaretoken]") as HTMLInputElement)
      ?.value ||
    ""
  );
}

async function updateProfile() {
  profileMsg.value = { type: "", text: "" };
  const formData = new FormData();
  formData.append("first_name", first_name.value);
  formData.append("last_name", last_name.value);

  try {
    const res = await fetch("/api/auth/profile", {
      method: "POST",
      headers: { "X-CSRFToken": getCsrfToken() },
      credentials: "include",
      body: formData,
    });
    if (res.ok) {
      const data = await res.json();
      account.value = data;
      profileMsg.value = {
        type: "success",
        text: t("account.profile_updated"),
      };
    } else {
      const err = await res.json();
      profileMsg.value = {
        type: "danger",
        text: err.detail || t("misc.error"),
      };
    }
  } catch (err) {
    profileMsg.value = { type: "danger", text: String(err) };
  }
}

async function changePassword() {
  passwordMsg.value = { type: "", text: "" };
  if (new_password.value !== confirm_password.value) {
    passwordMsg.value = { type: "danger", text: t("misc.error") };
    return;
  }

  const formData = new FormData();
  formData.append("old_password", old_password.value);
  formData.append("new_password", new_password.value);

  try {
    const res = await fetch("/api/auth/set-password", {
      method: "POST",
      headers: { "X-CSRFToken": getCsrfToken() },
      credentials: "include",
      body: formData,
    });
    if (res.ok) {
      passwordMsg.value = {
        type: "success",
        text: t("account.password_changed"),
      };
      old_password.value = "";
      new_password.value = "";
      confirm_password.value = "";
    } else {
      const err = await res.json();
      passwordMsg.value = {
        type: "danger",
        text: err.error || err.detail || t("misc.error"),
      };
    }
  } catch (err) {
    passwordMsg.value = { type: "danger", text: String(err) };
  }
}

onMounted(fetchAccount);
</script>

<template>
  <div v-if="!loading" class="account-page">
    <h1>{{ t("account.title") }}</h1>

    <div class="card flex-col gap-4">
      <h2>{{ t("account.profile") }}</h2>
      <form @submit.prevent="updateProfile" class="flex-col gap-4">
        <div>
          <label>{{ t("login.username") }}</label>
          <input
            class="input input-disabled"
            :value="account?.username"
            disabled
          />
        </div>
        <div class="flex gap-4">
          <div class="flex-1">
            <label>{{ t("account.first_name") }}</label>
            <input class="input" v-model="first_name" type="text" />
          </div>
          <div class="flex-1">
            <label>{{ t("account.last_name") }}</label>
            <input class="input" v-model="last_name" type="text" />
          </div>
        </div>
        <div
          v-if="profileMsg.text"
          :style="{ color: `var(--color-${profileMsg.type})` }"
          class="text-sm"
        >
          {{ profileMsg.text }}
        </div>
        <button class="btn btn-primary" type="submit">
          {{ t("account.update_profile") }}
        </button>
      </form>
    </div>

    <div class="card flex-col gap-4">
      <h2>{{ t("account.change_password") }}</h2>
      <form @submit.prevent="changePassword" class="flex-col gap-4">
        <div>
          <label>{{ t("account.old_password") }}</label>
          <input
            class="input"
            v-model="old_password"
            type="password"
            required
          />
        </div>
        <div>
          <label>{{ t("account.new_password") }}</label>
          <input
            class="input"
            v-model="new_password"
            type="password"
            required
          />
        </div>
        <div>
          <label>{{ t("account.confirm_password") }}</label>
          <input
            class="input"
            v-model="confirm_password"
            type="password"
            required
          />
        </div>
        <div
          v-if="passwordMsg.text"
          :style="{ color: `var(--color-${passwordMsg.type})` }"
          class="text-sm"
        >
          {{ passwordMsg.text }}
        </div>
        <button class="btn btn-primary" type="submit">
          {{ t("account.change_password") }}
        </button>
      </form>
    </div>
  </div>
  <div v-else class="flex items-center justify-center py-8">
    {{ t("btn.loading") }}
  </div>
</template>

<style scoped>
.account-page {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  max-width: 600px;
  margin: 0 auto;
}

.input-disabled {
  background-color: var(--color-bg-mute);
}
</style>
