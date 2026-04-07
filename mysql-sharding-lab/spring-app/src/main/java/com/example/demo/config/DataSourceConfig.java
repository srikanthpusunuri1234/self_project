package com.example.demo.config;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import javax.sql.DataSource;

@Configuration
public class DataSourceConfig {

    @Bean("shard0")
    public JdbcTemplate shard0() {
        return new JdbcTemplate(createDS("jdbc:mysql://localhost:6033/user_db_0"));
    }

    @Bean("shard1")
    public JdbcTemplate shard1() {
        return new JdbcTemplate(createDS("jdbc:mysql://localhost:6033/user_db_1"));
    }

    private DataSource createDS(String url) {
        DriverManagerDataSource ds = new DriverManagerDataSource();
        ds.setUrl(url);
        ds.setUsername("app");
        ds.setPassword("app123");
        return ds;
    }
}