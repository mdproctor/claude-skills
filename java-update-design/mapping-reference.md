# java-update-design — Mapping Reference

Referenced by `java-update-design/SKILL.md` Step 4.

---

## Code Change → DESIGN.md Section

| Code change | Likely DESIGN.md section |
|---|---|
| New REST endpoint / controller | API / Endpoints |
| New service or module | Components / Architecture |
| New external dependency | Dependencies / Technology Stack |
| DB schema / entity change | Data Model |
| New configuration property | Configuration |
| Breaking API change | Breaking Changes / Migration |
| Removed component | Components (mark as removed) |
| New async flow (queue, event, scheduler) | Architecture / Data Flow |
| New security constraint (auth, role, filter) | Security |
| New cross-cutting concern (caching, retry, tracing) | Architecture / Cross-cutting Concerns |
| Module extracted into separate service/jar | Components (note boundary change) |
| New DTO / request-response contract | API / Data Contracts |
| Interface or abstract class added | Components / Extension Points |

---

## Java Annotations → Architectural Signal

| Annotation / Pattern | Architectural signal |
|---|---|
| `@RestController`, `@RequestMapping` | New or changed public API surface |
| `@Service`, `@Component` | New application logic component |
| `@Repository`, `@Entity`, `@Table` | Data layer or schema change |
| `@Scheduled`, `@Async` | New background job or async flow |
| `@KafkaListener`, `@RabbitListener` | New message-driven component |
| `@FeignClient`, `@RestTemplate` | New external service integration |
| `@Configuration`, `@Bean` | New infrastructure wiring |
| `@PreAuthorize`, `@Secured` | Security policy change |
| `@Cacheable`, `@CacheEvict` | Caching strategy introduced or changed |
| New `*Exception` class + `@ControllerAdvice` | New error handling contract |
| New package (e.g. `adapter/`, `port/`, `domain/`) | Possible architectural layer added |
| `pom.xml` / `build.gradle` dependency added | New external dependency — check if it implies a pattern (e.g. adding Resilience4j implies circuit breaking) |
