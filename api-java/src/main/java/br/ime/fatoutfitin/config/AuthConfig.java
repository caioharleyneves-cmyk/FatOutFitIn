package br.ime.fatoutfitin.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.HandlerInterceptor;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import br.ime.fatoutfitin.service.AuthService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

@Configuration
public class AuthConfig implements WebMvcConfigurer {
    private final AuthService auth;

    public AuthConfig(AuthService auth) { this.auth = auth; }

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new HandlerInterceptor() {
            @Override
            public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
                if (!"OPTIONS".equals(request.getMethod())) {
                    request.setAttribute("usuarioId", auth.usuarioId(request.getHeader("Authorization")));
                }
                return true;
            }
        }).addPathPatterns("/api/treinos", "/api/treinos/**", "/api/cardios", "/api/cardios/**",
                "/api/catalogo-treinos", "/api/catalogo-treinos/**");
    }
}
