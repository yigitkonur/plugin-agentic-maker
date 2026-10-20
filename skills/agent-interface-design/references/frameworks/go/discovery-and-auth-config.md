# Go: Effective Config and Provider Abstraction

> Read when: you are implementing `config show --effective` with per-value sources, or a normalized multi-provider resource model in a Go CLI.

The rules are in `../../cli/config-and-env.md`.

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#Implementation Example~3 -->
## Effective config with sources

```go
type ConfigValue struct {
    Value  interface{} `json:"value"`
    Source string      `json:"source"`
}

type EffectiveConfig struct {
    APIUrl  ConfigValue `json:"api_url"`
    Timeout ConfigValue `json:"timeout"`
    Profile ConfigValue `json:"profile"`
}

func loadEffectiveConfig(cmd *cobra.Command) (*EffectiveConfig, error) {
    cfg := &EffectiveConfig{}

    // API URL resolution
    if url, _ := cmd.Flags().GetString("api-url"); url != "" {
        cfg.APIUrl = ConfigValue{Value: url, Source: "flag"}
    } else if url := os.Getenv("MYCLI_API_URL"); url != "" {
        cfg.APIUrl = ConfigValue{Value: url, Source: "environment_variable"}
    } else if fileCfg, err := loadConfigFile(); err == nil && fileCfg.APIUrl != "" {
        cfg.APIUrl = ConfigValue{Value: fileCfg.APIUrl, Source: "config_file"}
    } else {
        cfg.APIUrl = ConfigValue{Value: "https://api.example.com", Source: "default"}
    }

    // Similar pattern for other config values...

    return cfg, nil
}

func showEffectiveConfig(cmd *cobra.Command, cfg *EffectiveConfig) error {
    if jsonOutput, _ := cmd.Flags().GetBool("json"); jsonOutput {
        enc := json.NewEncoder(os.Stdout)
        enc.SetIndent("", "  ")
        return enc.Encode(map[string]interface{}{
            "ok": true, "command": "config show", "schema_version": "1.0",
            "result": cfg, "meta": map[string]interface{}{},
        })
    }

    fmt.Printf("api_url: %v (from %s)\n", cfg.APIUrl.Value, cfg.APIUrl.Source)
    fmt.Printf("timeout: %v (from %s)\n", cfg.Timeout.Value, cfg.Timeout.Source)
    return nil
}
```

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#Implementation Example~4 -->
## Provider interface and normalization

```go
type Resource struct {
    ID           string                 `json:"id"`
    Name         string                 `json:"name"`
    Provider     string                 `json:"provider"`
    Region       string                 `json:"region"`
    Status       string                 `json:"status"`
    ProviderData map[string]interface{} `json:"provider_data,omitempty"`
}

type Provider interface {
    Name() string
    ListResources(ctx context.Context, opts ListOptions) ([]Resource, error)
    GetResource(ctx context.Context, id string) (*Resource, error)
    CreateResource(ctx context.Context, spec ResourceSpec) (*Resource, error)
}

func getProvider(name string) (Provider, error) {
    switch name {
    case "aws":
        return NewAWSProvider()
    case "gcp":
        return NewGCPProvider()
    case "azure":
        return NewAzureProvider()
    default:
        return nil, fmt.Errorf("unknown provider: %s", name)
    }
}

// Normalize provider-specific data into common schema
func (p *AWSProvider) normalizeResource(awsResource *ec2.Instance) Resource {
    return Resource{
        ID:       *awsResource.InstanceId,
        Name:     getTag(awsResource.Tags, "Name"),
        Provider: "aws",
        Region:   p.region,
        Status:   normalizeStatus(*awsResource.State.Name),
        ProviderData: map[string]interface{}{
            "aws": map[string]interface{}{
                "arn":           buildARN(awsResource),
                "instance_type": *awsResource.InstanceType,
                "vpc_id":        *awsResource.VpcId,
            },
        },
    }
}
```
