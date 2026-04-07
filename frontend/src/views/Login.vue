<script setup lang="ts">
import { ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useI18n } from "../composables/useI18n";

const { t } = useI18n();
const router = useRouter();
const route = useRoute();

const username = ref("");
const password = ref("");
const errorMsg = ref("");

async function handleLogin() {
  errorMsg.value = "";
  try {
    const formData = new FormData();
    formData.append("username", username.value);
    formData.append("password", password.value);

    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: {
        "X-CSRFToken":
          (
            document.querySelector(
              "[name=csrfmiddlewaretoken]",
            ) as HTMLInputElement
          )?.value || "",
      },
      body: formData,
    });

    if (!res.ok) {
      errorMsg.value = t("login.error");
    } else {
      const next = route.query.next as string;
      router.push(next || "/");
    }
  } catch (err) {
    errorMsg.value = String(err);
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="card auth-card">
      <h2>{{ t("login.title") }}</h2>
      <form @submit.prevent="handleLogin" class="flex-col gap-4">
        <div>
          <label>{{ t("login.username") }}</label>
          <input class="input" v-model="username" type="text" required />
        </div>
        <div>
          <label>{{ t("login.password") }}</label>
          <input class="input" v-model="password" type="password" required />
        </div>
        <div v-if="errorMsg" class="text-center alert-danger">
          {{ errorMsg }}
        </div>
        <button class="btn btn-primary btn-block mt-4" type="submit">
          {{ t("login.submit") }}
        </button>
        <div class="text-center mt-4">
          <RouterLink to="/forgot-password" class="text-mute text-sm">{{
            t("login.forgot_password")
          }}</RouterLink>
        </div>
      </form>
    </div>
  </div>
</template>
