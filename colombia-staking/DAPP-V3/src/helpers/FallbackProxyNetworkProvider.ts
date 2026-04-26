/**
 * FallbackProxyNetworkProvider - wraps ProxyNetworkProvider with automatic failover
 * 
 * Primary: Colombia Kepler proxy (colombia-staking.co/gateway)
 * Fallback: Public MultiversX gateway (gateway.multiversx.com)
 * 
 * Usage: replace `new ProxyNetworkProvider(gatewayAddress)` with `new FallbackProxyNetworkProvider()`
 */

import { ProxyNetworkProvider } from '@multiversx/sdk-network-providers';
import type { IContractQuery } from '@multiversx/sdk-network-providers/out/interface';

const PRIMARY = 'https://colombia-staking.co/gateway';
const SECONDARY = 'https://gateway.multiversx.com';

export class FallbackProxyNetworkProvider {
  private primary: ProxyNetworkProvider;
  private secondary: ProxyNetworkProvider;
  private failedEndpoints = new Set<string>();

  constructor() {
    this.primary = new ProxyNetworkProvider(PRIMARY);
    this.secondary = new ProxyNetworkProvider(SECONDARY);
  }

  private async execute<T>(
    fn: (provider: ProxyNetworkProvider) => Promise<T>
  ): Promise<T> {
    // Try primary unless it's known to be down
    if (!this.failedEndpoints.has(PRIMARY)) {
      try {
        return await fn(this.primary);
      } catch (err) {
        console.warn('[FallbackProvider] Primary gateway failed, trying secondary:', err);
        this.failedEndpoints.add(PRIMARY);
      }
    }

    // Fall back to secondary
    if (!this.failedEndpoints.has(SECONDARY)) {
      try {
        return await fn(this.secondary);
      } catch (err) {
        console.error('[FallbackProvider] Both gateways failed:', err);
        this.failedEndpoints.add(SECONDARY);
        throw err;
      }
    }

    // Both known failed - try primary anyway (it might have recovered)
    try {
      return await fn(this.primary);
    } catch (err) {
      throw err;
    }
  }

  async queryContract(query: IContractQuery) {
    return this.execute((p) => p.queryContract(query));
  }

  async getNetworkConfig() {
    return this.execute((p) => p.getNetworkConfig());
  }

  async getCurrentBlockHash() {
    return this.execute((p) => (p as any).getCurrentBlockHash());
  }

  async getCurrentBlockRound() {
    return this.execute((p) => (p as any).getCurrentBlockRound());
  }

  async getBlockByRound(round: number) {
    return this.execute((p) => (p as any).getBlockByRound(round));
  }

  async getAccount(address: any) {
    return this.execute((p) => p.getAccount(address));
  }

  async getTokenData(tokenIdentifier: string, address: any) {
    return this.execute((p) => (p as any).getTokenData(tokenIdentifier, address));
  }

  async getEsdtTokensRoles(address: any, tokenIdentifier: string) {
    return this.execute((p) => (p as any).getEsdtTokensRoles(address, tokenIdentifier));
  }

  async getAllEsdtTokens(address: any) {
    return this.execute((p) => (p as any).getAllEsdtTokens(address));
  }

  async getNonces(address: any, tokenIdentifier: string) {
    return this.execute((p) => (p as any).getNonces(address, tokenIdentifier));
  }

  async getEsdtBalance(address: any, tokenIdentifier: string) {
    return this.execute((p) => (p as any).getEsdtBalance(address, tokenIdentifier));
  }

  async getBlock(hash: string) {
    return this.execute((p) => (p as any).getBlock(hash));
  }

  async getTransaction(hash: string) {
    return this.execute((p) => (p as any).getTransaction(hash));
  }

  async getVmQuery(params: { scAddress: string; funcName: string; args?: any[]; caller?: string; value?: string }) {
    return this.execute((p) => (p as any).getVmQuery(params));
  }

  // Health check - resets failed endpoints if primary recovers
  async isPrimaryHealthy(): Promise<boolean> {
    try {
      await this.primary.getNetworkConfig();
      this.failedEndpoints.delete(PRIMARY);
      return true;
    } catch {
      return false;
    }
  }
}
